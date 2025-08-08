import asyncio
import json
from typing import Any, AsyncIterator, Dict, List


class EventBus:
    def __init__(self) -> None:
        self._subscribers: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    async def publish(self, event: Dict[str, Any]) -> None:
        async with self._lock:
            for q in list(self._subscribers):
                # best-effort non-blocking put
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    # drop if slow consumer
                    pass

    async def subscribe(self) -> AsyncIterator[Dict[str, Any]]:
        q: asyncio.Queue = asyncio.Queue(maxsize=500)
        async with self._lock:
            self._subscribers.append(q)
        try:
            while True:
                event = await q.get()
                yield event
        finally:
            async with self._lock:
                if q in self._subscribers:
                    self._subscribers.remove(q)


bus = EventBus()


def format_sse(event_type: str, data: Dict[str, Any]) -> bytes:
    payload = json.dumps(data, separators=(",", ":"))
    return f"event: {event_type}\ndata: {payload}\n\n".encode("utf-8")


