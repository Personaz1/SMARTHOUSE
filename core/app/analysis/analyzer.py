import asyncio
import time
from typing import Any, Dict, Optional

from ..state.context import HomeContextManager
from ..events import bus
from ..metrics import analysis_ticks_total, analysis_insights_total


class BackgroundAnalyzer:
    def __init__(self, context: HomeContextManager) -> None:
        self._context = context
        self._task: Optional[asyncio.Task] = None

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

    async def _run(self) -> None:
        # Very lightweight periodic analysis loop
        while True:
            await asyncio.sleep(2.0)
            analysis_ticks_total.inc()
            snap: Dict[str, Any] = self._context.snapshot()
            # Example heuristic: detect lights on with no presence in zone
            zones = snap.get("zones", {})
            for room, z in zones.items():
                light = z.get("light")
                presence = z.get("presence", False)
                if light == "ON" and presence is False:
                    insight = {
                        "type": "insight",
                        "kind": "waste_light",
                        "room": room,
                        "ts": time.time(),
                    }
                    analysis_insights_total.labels(kind="waste_light").inc()
                    await bus.publish(insight)


