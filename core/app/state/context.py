import asyncio
import json
import time
from typing import Any, Dict, Optional

from aiomqtt import Client as MqttClient


class HomeContextManager:
    def __init__(
        self,
        host: str,
        port: int,
        username: Optional[str],
        password: Optional[str],
        devices_registry: Dict[str, Any],
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._client: Optional[MqttClient] = None
        self._lock = asyncio.Lock()
        self._registry = devices_registry or {}
        self._state: Dict[str, Any] = {
            "security_mode": "home",
            "occupancy": "home",
            "energy_mode": "normal",
            "comfort": {},
            "zones": {},
            "health": {"mqtt": "ok"},
            "devices": {},
            "ts": time.time(),
        }
        self._task: Optional[asyncio.Task] = None

    def snapshot(self) -> Dict[str, Any]:
        return self._state.copy()

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._client is not None:
            await self._client.__aexit__(None, None, None)
            self._client = None

    async def _run(self) -> None:
        # own MQTT client to avoid interference with RPC publish+wait
        self._client = MqttClient(
            hostname=self._host,
            port=self._port,
            username=self._username,
            password=self._password,
            client_id="smarthouse-context",
        )
        await self._client.__aenter__()
        async with self._client.messages() as messages:
            await self._client.subscribe("home/#", qos=1)
            await self._client.subscribe("vision/events/#", qos=1)
            async for message in messages:
                raw_topic = getattr(message, "topic", "")
                topic = raw_topic.value if hasattr(raw_topic, "value") else raw_topic
                try:
                    payload = message.payload.decode("utf-8")
                    data = json.loads(payload)
                except Exception:
                    continue
                await self._ingest(topic, data)

    async def _ingest(self, topic: str, data: Dict[str, Any]) -> None:
        parts = topic.split("/")
        if parts[0] == "vision" and parts[1] == "events":
            entity_id = f"{parts[0]}/{parts[1]}/{parts[2]}"
            async with self._lock:
                self._state["devices"][entity_id] = data
                self._state["ts"] = time.time()
            return

        if len(parts) < 4:
            return
        kind, _, entity_id, path = parts[0], parts[1], parts[2], parts[3]
        if kind == "home" and path == "state":
            async with self._lock:
                if entity_id not in self._state["devices"]:
                    self._state["devices"][entity_id] = {}
                self._state["devices"][entity_id] = data
                self._state["ts"] = time.time()
                device_meta = self._registry.get(entity_id)
                if device_meta:
                    room = device_meta.get("room")
                    dtype = device_meta.get("type")
                    if room:
                        zone = self._state["zones"].setdefault(room, {})
                        if dtype == "light":
                            zone["light"] = data.get("state")
                            if "brightness" in data:
                                zone["brightness"] = data.get("brightness")
                        elif dtype == "lock":
                            zone["lock"] = data.get("state")
                        elif dtype == "sensor":
                            if data.get("type") == "motion":
                                zone["presence"] = bool(data.get("value"))
                            if data.get("type") == "illuminance":
                                zone["illuminance"] = data.get("lux")

    async def upsert_device_state(self, entity_id: str, data: Dict[str, Any]) -> None:
        async with self._lock:
            self._state["devices"][entity_id] = data
            self._state["ts"] = time.time()
            device_meta = self._registry.get(entity_id)
            if device_meta:
                room = device_meta.get("room")
                dtype = device_meta.get("type")
                if room:
                    zone = self._state["zones"].setdefault(room, {})
                    if dtype == "light":
                        zone["light"] = data.get("state")
                        if "brightness" in data:
                            zone["brightness"] = data.get("brightness")
                    elif dtype == "lock":
                        zone["lock"] = data.get("state")


