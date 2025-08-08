import json
import os
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import Draft202012Validator


class ConfigLoader:
    def __init__(self, config_dir: str) -> None:
        self.config_dir = Path(config_dir)
        if not self.config_dir.exists():
            raise FileNotFoundError(f"Config dir not found: {self.config_dir}")

    def _load_json(self, filename: str) -> Any:
        path = self.config_dir / filename
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _validate(self, data: Any, schema_name: str) -> None:
        schema = self._load_json(schema_name)
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
        if errors:
            messages = [f"{list(err.path)}: {err.message}" for err in errors]
            raise ValueError(f"Config validation failed for {schema_name}:\n" + "\n".join(messages))

    def load_devices(self) -> Dict[str, Dict[str, Any]]:
        devices_list: List[Dict[str, Any]] = self._load_json("devices.json")
        self._validate(devices_list, "devices.schema.json")
        devices_map = {d["id"]: d for d in devices_list}
        return devices_map

    def load_rules(self) -> List[Dict[str, Any]]:
        rules_list: List[Dict[str, Any]] = self._load_json("rules.json")
        self._validate(rules_list, "rules.schema.json")
        return rules_list


