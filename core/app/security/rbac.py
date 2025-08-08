from typing import Dict, List


class RBAC:
    def __init__(self, policy: Dict[str, List[str]] | None = None) -> None:
        self._policy = policy or {
            "admin": ["*"]
        }

    def is_allowed(self, role: str, tool_name: str) -> bool:
        allowed = self._policy.get(role, [])
        return "*" in allowed or tool_name in allowed


