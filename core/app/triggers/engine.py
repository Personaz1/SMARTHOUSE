import asyncio
import datetime as dt
import json
import time
from typing import Any, Dict, List, Optional

from ..state.context import HomeContextManager
from ..tools.smarthome import SmartHomeTools
from ..metrics import trigger_firings_total


class TriggerEngine:
    def __init__(self, context: HomeContextManager, tools: SmartHomeTools, rules: List[Dict[str, Any]]):
        self._context = context
        self._tools = tools
        self._rules = rules
        self._task: Optional[asyncio.Task] = None
        self._last_fire: Dict[str, float] = {}
        self._debounce_until: Dict[str, float] = {}
        self._throttle_until: Dict[str, float] = {}

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

    def set_rules(self, rules: List[Dict[str, Any]]) -> None:
        self._rules = rules
        self._last_fire.clear()

    async def _run(self) -> None:
        while True:
            await asyncio.sleep(0.25)
            snapshot = self._context.snapshot()
            for rule in self._rules:
                try:
                    await self._maybe_fire(rule, snapshot)
                except Exception:
                    continue

    async def _maybe_fire(self, rule: Dict[str, Any], snapshot: Dict[str, Any]) -> None:
        rule_id = rule.get("id")
        safety = rule.get("safety", {})
        rate_limit = float(safety.get("rate_limit_per_min", 0))
        now = time.time()
        if rate_limit > 0:
            last = self._last_fire.get(rule_id, 0)
            min_interval = 60.0 / max(rate_limit, 1)
            if now - last < min_interval:
                return

        # guards: debounce / throttle windows
        guards = rule.get("guards", {})
        debounce_ms = int(guards.get("debounce_ms", 0))
        throttle_per_min = float(guards.get("throttle_per_min", 0))
        now_ms = now * 1000
        if debounce_ms > 0 and now_ms < self._debounce_until.get(rule_id, 0):
            return
        if throttle_per_min > 0:
            min_interval_ms = 60000.0 / max(throttle_per_min, 1)
            if now_ms < self._throttle_until.get(rule_id, 0):
                return

        rtype = rule.get("type")
        if rtype == "time":
            after = rule.get("after")
            if after and not self._is_after_localtime(after):
                return
        elif rtype == "sensor":
            cond = rule.get("condition", {})
            equals = cond.get("equals", {})
            ok = False
            if "sensor_id" in cond:
                sensor_id = cond.get("sensor_id")
                sensor_state = snapshot.get("devices", {}).get(sensor_id)
                ok = self._subset_match(equals, sensor_state or {})
            elif "topic" in cond:
                # For now, read last event cached as a device by topic name if present
                topic = cond.get("topic")
                sensor_state = snapshot.get("devices", {}).get(topic)
                ok = self._subset_match(equals, sensor_state or {})
            after = cond.get("after")
            if after and not self._is_after_localtime(after):
                ok = False
            dur = cond.get("for")
            if dur:
                # ISO8601 like PT00M30S -> seconds
                seconds = self._parse_iso8601_duration(dur)
                # naive: require last_fire older than seconds
                if (now - self._last_fire.get(rule_id, 0)) < seconds:
                    ok = False
            if not ok:
                return
        else:
            return

        # Fire actions
        # execute with retry/backoff
        retry = guards.get("retry", {})
        max_attempts = int(retry.get("max", 1))
        backoff_ms = int(retry.get("backoff_ms", 250))
        fired_ok = True
        for action in rule.get("actions", []):
            tool = action.get("tool")
            args = action.get("args", {})
            attempt = 0
            while True:
                try:
                    await self._invoke_tool(tool, args)
                    break
                except Exception:
                    attempt += 1
                    if attempt >= max_attempts:
                        fired_ok = False
                        break
                    await asyncio.sleep(backoff_ms / 1000.0)

        self._last_fire[rule_id] = now
        if debounce_ms > 0:
            self._debounce_until[rule_id] = now_ms + debounce_ms
        if throttle_per_min > 0:
            self._throttle_until[rule_id] = now_ms + (60000.0 / max(throttle_per_min, 1))
        trigger_firings_total.labels(rule_id=rule_id, result=("ok" if fired_ok else "err")).inc()

    async def _invoke_tool(self, tool: str, args: Dict[str, Any]) -> None:
        if tool == "control_light":
            await self._tools.control_light(
                device_id=args["device_id"],
                state=bool(args.get("state", True)),
                brightness=args.get("brightness"),
            )
        elif tool == "notify":
            # placeholder
            return

    def _is_after_localtime(self, hhmm: str) -> bool:
        now = dt.datetime.now().time()
        h, m = map(int, hhmm.split(":"))
        return (now.hour, now.minute) >= (h, m)

    def _subset_match(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
        try:
            for k, v in expected.items():
                if actual.get(k) != v:
                    return False
            return True
        except Exception:
            return False

    def _parse_iso8601_duration(self, s: str) -> float:
        # minimal PTxxMxxS parser
        if not s.startswith("PT"):
            return 0.0
        s = s[2:]
        minutes = 0
        seconds = 0
        if "M" in s:
            m_part, s_part = s.split("M", 1)
            minutes = int(m_part or 0)
            s = s_part
        if s.endswith("S"):
            seconds = int(s[:-1] or 0)
        return minutes * 60 + seconds


