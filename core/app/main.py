import os
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from .config import ConfigLoader
from .integration.mqtt_client import AsyncMqttClient
from .tools.smarthome import SmartHomeTools
from .state.context import HomeContextManager
from .security.rbac import RBAC
from .audit import AuditLogger
from .triggers.engine import TriggerEngine
from .models import (
    ControlLightReq,
    SetThermostatReq,
    DeviceIdReq,
    CoverSetPositionReq,
    ArmSecurityReq,
    CameraSnapshotReq,
)
from .metrics import tool_calls_total, tool_call_latency_ms, agent_commands_total
from .agent.supervisor import Supervisor
from .metrics import rules_version
from .api_router import router as router_api
from .events import bus, format_sse
from .analysis.analyzer import BackgroundAnalyzer
from .storage.db import EventStore


app = FastAPI(title="ΔΣ Guardian Core", version="0.1.0")
# CORS for UI dev/prod hosts
allowed_origins = os.getenv("UI_CORS_ORIGINS", "http://localhost:8080,http://ui:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
Instrumentator().instrument(app).expose(app, include_in_schema=False, endpoint="/metrics")
app.include_router(router_api)
static_dir = Path(os.getenv("STATIC_DIR", "/configs/static"))
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


class AppState:
    config_loader: Optional[ConfigLoader] = None
    devices: Optional[Dict[str, Dict[str, Any]]] = None
    rules: Optional[Any] = None
    mqtt: Optional[AsyncMqttClient] = None
    tools: Optional[SmartHomeTools] = None
    context: Optional[HomeContextManager] = None
    rbac: RBAC = RBAC()
    audit: AuditLogger = AuditLogger()
    triggers: Optional[TriggerEngine] = None
    supervisor: Optional[Supervisor] = None
    analyzer: Optional[BackgroundAnalyzer] = None
    store: Optional[EventStore] = None
    boot_ts: float = time.time()


state = AppState()


@app.on_event("startup")
async def on_startup() -> None:
    config_dir = os.getenv("CONFIG_DIR", "/configs")
    state.config_loader = ConfigLoader(config_dir=config_dir)
    state.devices = state.config_loader.load_devices()
    state.rules = state.config_loader.load_rules()

    mqtt_host = os.getenv("MQTT_HOST", "mosquitto")
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_username = os.getenv("MQTT_USERNAME", "") or None
    mqtt_password = os.getenv("MQTT_PASSWORD", "") or None

    state.mqtt = AsyncMqttClient(
        host=mqtt_host,
        port=mqtt_port,
        username=mqtt_username,
        password=mqtt_password,
        client_id="smarthouse-core",
    )
    await state.mqtt.connect()

    state.tools = SmartHomeTools(mqtt=state.mqtt, devices=state.devices)
    state.context = HomeContextManager(
        host=mqtt_host,
        port=mqtt_port,
        username=mqtt_username,
        password=mqtt_password,
        devices_registry=state.devices,
    )
    await state.context.start()
    state.triggers = TriggerEngine(context=state.context, tools=state.tools, rules=state.rules or [])
    await state.triggers.start()
    state.supervisor = Supervisor(state.tools)
    state.analyzer = BackgroundAnalyzer(state.context)
    await state.analyzer.start()
    state.store = EventStore(path=os.getenv("DB_PATH", "/data/core.db"))
    await state.store.start(bus)
    # announce startup
    await bus.publish({"type": "state_update", "snapshot": state.context.snapshot()})


@app.on_event("shutdown")
async def on_shutdown() -> None:
    if state.mqtt is not None:
        await state.mqtt.disconnect()
    if state.context is not None:
        await state.context.stop()
    if state.triggers is not None:
        await state.triggers.stop()
    if state.analyzer is not None:
        await state.analyzer.stop()
    if state.store is not None:
        await state.store.stop()
    state.supervisor = None


@app.get("/ui/stream")
async def ui_stream() -> StreamingResponse:
    async def event_generator():
        # heartbeat first
        yield format_sse("heartbeat", {"ts": time.time()})
        async for ev in bus.subscribe():
            etype = ev.get("type", "event")
            yield format_sse(etype, ev)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/chat/stream")
async def chat_stream(q: str) -> StreamingResponse:
    async def gen():
        text = f"Ответ на: {q}"
        for token in text.split(" "):
            yield format_sse("chunk", {"text": token + " "})
            await asyncio.sleep(0.02)
        yield format_sse("done", {"ok": True})
    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/history/events")
async def history_events(limit: int = 200, etype: Optional[str] = None) -> Dict[str, Any]:
    if state.store is None:
        raise HTTPException(status_code=503, detail="Store not ready")
    rows = await state.store.recent(limit=limit, etype=etype)
    return {"events": rows}


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "uptime_s": round(time.time() - state.boot_ts, 1),
        "devices": len(state.devices or {}),
        "rules": len(state.rules or []),
    }


@app.get("/state")
async def get_state() -> Dict[str, Any]:
    return state.context.snapshot() if state.context else {}


@app.get("/tools/camera_snapshot_url")
async def tool_camera_snapshot_url(camera_id: str) -> Dict[str, Any]:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")
    res = await state.tools.get_snapshot_url(camera_id)
    return res


@app.post("/agent/command")
async def agent_command(payload: Dict[str, Any]) -> JSONResponse:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")

    trace_id = str(uuid.uuid4())
    command = payload.get("command")
    dry_run = bool(payload.get("dry_run", False))
    role = payload.get("role", "admin")

    result: Dict[str, Any] = {"trace_id": trace_id, "status": "accepted"}

    # Structured tool-call
    if isinstance(command, dict) and command.get("tool") == "control_light":
        if not state.rbac.is_allowed(role, "control_light"):
            raise HTTPException(status_code=403, detail="Forbidden")
        if dry_run:
            result["dry_run"] = True
        else:
            args = command.get("args", {})
            device_id = args.get("device_id")
            state_on = bool(args.get("state", True))
            brightness = args.get("brightness")
            start = time.time()
            tool_res = await state.tools.control_light(device_id=device_id, state=state_on, brightness=brightness)
            latency_ms = (time.time() - start) * 1000
            state.audit.log(actor="api", role=role, action="control_light", args=args, result="ok", latency_ms=latency_ms, trace_id=trace_id)
            tool_calls_total.labels(tool="control_light", result="ok").inc()
            tool_call_latency_ms.labels(tool="control_light").observe(latency_ms)
            result.update({"result": tool_res, "status": "ok"})
        agent_commands_total.labels(intent="structured", result="ok").inc()
        return JSONResponse(result)

    # Intent-driven plan via Supervisor
    if isinstance(command, str):
        if not state.supervisor:
            raise HTTPException(status_code=503, detail="Supervisor not ready")
        plan = await state.supervisor.plan_from_intent(command)
        steps = await state.supervisor.execute_plan(plan, dry_run=dry_run, require_confirm=bool(payload.get("confirm", False)))
        result.update({"status": "ok", "steps": steps})
        agent_commands_total.labels(intent="react", result="ok").inc()
        return JSONResponse(result)

    result.update({"status": "not_implemented"})
    agent_commands_total.labels(intent="unknown", result="accepted").inc()
    return JSONResponse(result, status_code=202)


@app.get("/devices")
async def list_devices() -> Dict[str, Any]:
    return {"devices": list((state.devices or {}).values())}


@app.get("/device/{device_id}")
async def get_device(device_id: str) -> Dict[str, Any]:
    dev = (state.devices or {}).get(device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found")
    return dev


@app.get("/config/devices")
async def get_config_devices() -> Dict[str, Any]:
    return {"devices": state.devices or {}}


@app.get("/config/rules")
async def get_config_rules() -> Dict[str, Any]:
    return {"rules": state.rules or []}


@app.post("/tools/control_light")
async def tool_control_light(payload: ControlLightReq, request: Request) -> Dict[str, Any]:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")
    role = request.headers.get("X-Role", "admin")
    start = time.time()
    res = await state.tools.control_light(payload.device_id, payload.state, payload.brightness)
    latency_ms = (time.time() - start) * 1000
    state.audit.log(actor="api", role=role, action="control_light", args=payload.model_dump(), result="ok", latency_ms=latency_ms, trace_id=None)
    tool_calls_total.labels(tool="control_light", result="ok").inc()
    tool_call_latency_ms.labels(tool="control_light").observe(latency_ms)
    return {"result": res}


@app.post("/tools/set_thermostat")
async def tool_set_thermostat(payload: SetThermostatReq, request: Request) -> Dict[str, Any]:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")
    role = request.headers.get("X-Role", "admin")
    start = time.time()
    res = await state.tools.set_thermostat(payload.device_id, float(payload.temperature))
    latency_ms = (time.time() - start) * 1000
    state.audit.log(actor="api", role=role, action="set_thermostat", args=payload.model_dump(), result="ok", latency_ms=latency_ms, trace_id=None)
    tool_calls_total.labels(tool="set_thermostat", result="ok").inc()
    tool_call_latency_ms.labels(tool="set_thermostat").observe(latency_ms)
    return {"result": res}


@app.post("/tools/lock_door")
async def tool_lock_door(payload: DeviceIdReq, request: Request) -> Dict[str, Any]:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")
    role = request.headers.get("X-Role", "admin")
    start = time.time()
    res = await state.tools.lock_door(payload.device_id)
    latency_ms = (time.time() - start) * 1000
    state.audit.log(actor="api", role=role, action="lock_door", args=payload.model_dump(), result="ok", latency_ms=latency_ms, trace_id=None)
    tool_calls_total.labels(tool="lock_door", result="ok").inc()
    tool_call_latency_ms.labels(tool="lock_door").observe(latency_ms)
    return {"result": res}


@app.post("/tools/unlock_door")
async def tool_unlock_door(payload: DeviceIdReq, request: Request) -> Dict[str, Any]:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")
    role = request.headers.get("X-Role", "admin")
    start = time.time()
    res = await state.tools.unlock_door(payload.device_id)
    latency_ms = (time.time() - start) * 1000
    state.audit.log(actor="api", role=role, action="unlock_door", args=payload.model_dump(), result="ok", latency_ms=latency_ms, trace_id=None)
    tool_calls_total.labels(tool="unlock_door", result="ok").inc()
    tool_call_latency_ms.labels(tool="unlock_door").observe(latency_ms)
    return {"result": res}


@app.post("/tools/cover_set_position")
async def tool_cover_set_position(payload: CoverSetPositionReq, request: Request) -> Dict[str, Any]:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")
    role = request.headers.get("X-Role", "admin")
    start = time.time()
    res = await state.tools.cover_set_position(payload.device_id, int(payload.position))
    latency_ms = (time.time() - start) * 1000
    state.audit.log(actor="api", role=role, action="cover_set_position", args=payload.model_dump(), result="ok", latency_ms=latency_ms, trace_id=None)
    tool_calls_total.labels(tool="cover_set_position", result="ok").inc()
    tool_call_latency_ms.labels(tool="cover_set_position").observe(latency_ms)
    return {"result": res}


@app.post("/tools/switch_on")
async def tool_switch_on(payload: DeviceIdReq, request: Request) -> Dict[str, Any]:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")
    role = request.headers.get("X-Role", "admin")
    start = time.time()
    res = await state.tools.switch_on(payload.device_id)
    latency_ms = (time.time() - start) * 1000
    state.audit.log(actor="api", role=role, action="switch_on", args=payload.model_dump(), result="ok", latency_ms=latency_ms, trace_id=None)
    tool_calls_total.labels(tool="switch_on", result="ok").inc()
    tool_call_latency_ms.labels(tool="switch_on").observe(latency_ms)
    return {"result": res}


@app.post("/tools/switch_off")
async def tool_switch_off(payload: DeviceIdReq, request: Request) -> Dict[str, Any]:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")
    role = request.headers.get("X-Role", "admin")
    start = time.time()
    res = await state.tools.switch_off(payload.device_id)
    latency_ms = (time.time() - start) * 1000
    state.audit.log(actor="api", role=role, action="switch_off", args=payload.model_dump(), result="ok", latency_ms=latency_ms, trace_id=None)
    tool_calls_total.labels(tool="switch_off", result="ok").inc()
    tool_call_latency_ms.labels(tool="switch_off").observe(latency_ms)
    return {"result": res}


@app.post("/tools/siren_on")
async def tool_siren_on(payload: DeviceIdReq, request: Request) -> Dict[str, Any]:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")
    role = request.headers.get("X-Role", "admin")
    start = time.time()
    res = await state.tools.siren_on(payload.device_id)
    latency_ms = (time.time() - start) * 1000
    state.audit.log(actor="api", role=role, action="siren_on", args=payload.model_dump(), result="ok", latency_ms=latency_ms, trace_id=None)
    tool_calls_total.labels(tool="siren_on", result="ok").inc()
    tool_call_latency_ms.labels(tool="siren_on").observe(latency_ms)
    return {"result": res}


@app.post("/tools/siren_off")
async def tool_siren_off(payload: DeviceIdReq, request: Request) -> Dict[str, Any]:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")
    role = request.headers.get("X-Role", "admin")
    start = time.time()
    res = await state.tools.siren_off(payload.device_id)
    latency_ms = (time.time() - start) * 1000
    state.audit.log(actor="api", role=role, action="siren_off", args=payload.model_dump(), result="ok", latency_ms=latency_ms, trace_id=None)
    tool_calls_total.labels(tool="siren_off", result="ok").inc()
    tool_call_latency_ms.labels(tool="siren_off").observe(latency_ms)
    return {"result": res}


@app.post("/tools/arm_security")
async def tool_arm_security(payload: ArmSecurityReq, request: Request) -> Dict[str, Any]:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")
    role = request.headers.get("X-Role", "admin")
    mode = payload.mode or "away"
    start = time.time()
    res = await state.tools.arm_security(mode)
    latency_ms = (time.time() - start) * 1000
    state.audit.log(actor="api", role=role, action="arm_security", args=payload.model_dump(), result="ok", latency_ms=latency_ms, trace_id=None)
    tool_calls_total.labels(tool="arm_security", result="ok").inc()
    tool_call_latency_ms.labels(tool="arm_security").observe(latency_ms)
    return {"result": res}


@app.post("/tools/disarm_security")
async def tool_disarm_security(request: Request) -> Dict[str, Any]:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")
    role = request.headers.get("X-Role", "admin")
    start = time.time()
    res = await state.tools.disarm_security()
    latency_ms = (time.time() - start) * 1000
    state.audit.log(actor="api", role=role, action="disarm_security", args={}, result="ok", latency_ms=latency_ms, trace_id=None)
    tool_calls_total.labels(tool="disarm_security", result="ok").inc()
    tool_call_latency_ms.labels(tool="disarm_security").observe(latency_ms)
    return {"result": res}


@app.post("/tools/camera_snapshot")
async def tool_camera_snapshot(payload: CameraSnapshotReq, request: Request) -> Dict[str, Any]:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")
    role = request.headers.get("X-Role", "admin")
    start = time.time()
    res = await state.tools.camera_snapshot(payload.camera_id)
    latency_ms = (time.time() - start) * 1000
    state.audit.log(actor="api", role=role, action="camera_snapshot", args=payload.model_dump(), result="ok", latency_ms=latency_ms, trace_id=None)
    tool_calls_total.labels(tool="camera_snapshot", result="ok").inc()
    tool_call_latency_ms.labels(tool="camera_snapshot").observe(latency_ms)
    return {"result": res}


@app.get("/tools/get_device_status")
async def tool_get_device_status(device_id: str, request: Request) -> Dict[str, Any]:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")
    role = request.headers.get("X-Role", "admin")
    start = time.time()
    res = await state.tools.get_device_status(device_id)
    latency_ms = (time.time() - start) * 1000
    state.audit.log(actor="api", role=role, action="get_device_status", args={"device_id": device_id}, result="ok", latency_ms=latency_ms, trace_id=None)
    return {"result": res}


@app.get("/tools/get_sensor_data")
async def tool_get_sensor_data(sensor_id: str, request: Request) -> Dict[str, Any]:
    if state.tools is None:
        raise HTTPException(status_code=503, detail="Tools not initialized")
    role = request.headers.get("X-Role", "admin")
    start = time.time()
    res = await state.tools.get_sensor_data(sensor_id)
    latency_ms = (time.time() - start) * 1000
    state.audit.log(actor="api", role=role, action="get_sensor_data", args={"sensor_id": sensor_id}, result="ok", latency_ms=latency_ms, trace_id=None)
    return {"result": res}


@app.post("/rules")
async def post_rules(rules: Dict[str, Any]) -> Dict[str, Any]:
    data = rules.get("rules") if isinstance(rules, dict) and "rules" in rules else rules
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Rules must be a list or {rules: [...]}" )
    state.rules = data
    if state.triggers:
        state.triggers.set_rules(data)
    rules_version.inc()
    return {"status": "ok", "count": len(data)}


@app.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str) -> Dict[str, Any]:
    if not isinstance(state.rules, list):
        raise HTTPException(status_code=404, detail="No rules loaded")
    new_rules = [r for r in state.rules if r.get("id") != rule_id]
    state.rules = new_rules
    if state.triggers:
        state.triggers.set_rules(new_rules)
    rules_version.inc()
    return {"status": "ok", "count": len(new_rules)}

