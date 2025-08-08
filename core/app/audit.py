import hashlib
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict


class AuditLogger:
    def __init__(self, log_dir: str = "/app/logs") -> None:
        self._path = Path(log_dir)
        self._path.mkdir(parents=True, exist_ok=True)
        self._file = self._path / "audit.log"

    def _hash_args(self, args: Any) -> str:
        try:
            blob = json.dumps(args, sort_keys=True, separators=(",", ":")).encode("utf-8")
        except Exception:
            blob = repr(args).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()[:16]

    def log(self, actor: str, role: str, action: str, args: Any, result: Any, latency_ms: float, trace_id: str | None = None) -> None:
        entry: Dict[str, Any] = {
            "timestamp": time.time(),
            "actor": actor,
            "role": role,
            "action": action,
            "args_hash": self._hash_args(args),
            "result": result,
            "latency_ms": round(latency_ms, 2),
            "trace_id": trace_id or str(uuid.uuid4()),
        }
        with self._file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")


