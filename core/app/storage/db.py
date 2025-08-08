import asyncio
import json
import aiosqlite
from typing import Any, Dict, Optional, List


class EventStore:
    def __init__(self, path: str = "/data/core.db") -> None:
        self._path = path
        self._db: Optional[aiosqlite.Connection] = None
        self._task: Optional[asyncio.Task] = None
        self._bus = None

    async def start(self, bus) -> None:
        self._bus = bus
        self._db = await aiosqlite.connect(self._path)
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                type TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            """
        )
        await self._db.commit()
        if self._task is None:
            self._task = asyncio.create_task(self._consume())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def _consume(self) -> None:
        assert self._bus is not None
        async for ev in self._bus.subscribe():
            etype = ev.get("type", "event")
            if etype == "heartbeat":
                continue
            ts = float(ev.get("ts") or 0.0)
            try:
                payload = json.dumps(ev, separators=(",", ":"))
            except Exception:
                continue
            try:
                await self._db.execute(
                    "INSERT INTO events (ts, type, payload) VALUES (?, ?, ?)",
                    (ts, etype, payload),
                )
                await self._db.commit()
            except Exception:
                # ignore db write errors to not break the loop
                pass

    async def recent(self, limit: int = 200, etype: Optional[str] = None) -> List[Dict[str, Any]]:
        assert self._db is not None
        q = "SELECT ts, type, payload FROM events"
        args: List[Any] = []
        if etype:
            q += " WHERE type = ?"
            args.append(etype)
        q += " ORDER BY id DESC LIMIT ?"
        args.append(int(limit))
        rows = []
        async with self._db.execute(q, args) as cur:
            async for ts, typ, payload in cur:
                try:
                    data = json.loads(payload)
                except Exception:
                    data = {"type": typ, "ts": ts}
                rows.append(data)
        return rows


