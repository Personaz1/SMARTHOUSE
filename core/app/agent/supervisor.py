import time
from typing import Any, Dict, List

from ..tools.smarthome import SmartHomeTools
from ..events import bus
from ..metrics import agent_step_latency_ms, critical_actions_total


CRITICAL_TOOLS = {"lock_door", "arm_security"}


class Supervisor:
    def __init__(self, tools: SmartHomeTools) -> None:
        self._tools = tools
        self._critical_window = []  # list of timestamps of critical actions

    def _allow_critical(self) -> bool:
        now = time.time()
        # keep only last 60 seconds
        self._critical_window = [t for t in self._critical_window if now - t < 60]
        return len(self._critical_window) < 3

    async def execute_plan(self, steps: List[Dict[str, Any]], dry_run: bool = False, require_confirm: bool = False) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for step in steps:
            tool = step.get("tool")
            args = step.get("args", {})
            start = time.time()
            if dry_run:
                results.append({"tool": tool, "args": args, "status": "dry_run"})
                continue
            if require_confirm and tool in CRITICAL_TOOLS:
                results.append({"tool": tool, "args": args, "status": "needs_confirm"})
                continue
            if tool in CRITICAL_TOOLS and not self._allow_critical():
                results.append({"tool": tool, "args": args, "status": "rate_limited"})
                continue
            try:
                out = await self._invoke(tool, args)
                latency_ms = (time.time() - start) * 1000
                agent_step_latency_ms.labels(tool=tool).observe(latency_ms)
                if tool in CRITICAL_TOOLS:
                    self._critical_window.append(time.time())
                    critical_actions_total.labels(tool=tool).inc()
                step = {"tool": tool, "args": args, "status": "ok", "lat_ms": round(latency_ms, 2), "result": out}
                results.append(step)
                await bus.publish({"type": "agent_step", **step, "ts": time.time()})
            except Exception as e:
                results.append({"tool": tool, "args": args, "status": "err", "error": str(e)})
                break
        return results

    async def plan_from_intent(self, intent: str) -> List[Dict[str, Any]]:
        # Minimal heuristic plan for "prepare house for night"
        if "ноч" in intent or "sleep" in intent or "night" in intent:
            return [
                {"tool": "control_light", "args": {"device_id": "light_living_main", "state": True, "brightness": 20}},
                {"tool": "arm_security", "args": {"mode": "night"}},
            ]
        # default empty
        return []

    async def _invoke(self, tool: str, args: Dict[str, Any]) -> Any:
        if tool == "control_light":
            return await self._tools.control_light(args["device_id"], bool(args.get("state", True)), args.get("brightness"))
        if tool == "lock_door":
            return await self._tools.lock_door(args["device_id"])
        if tool == "unlock_door":
            return await self._tools.unlock_door(args["device_id"])
        if tool == "cover_set_position":
            return await self._tools.cover_set_position(args["device_id"], int(args["position"]))
        if tool == "arm_security":
            return await self._tools.arm_security(args.get("mode", "away"))
        if tool == "disarm_security":
            return await self._tools.disarm_security()
        raise ValueError(f"Unknown tool: {tool}")


