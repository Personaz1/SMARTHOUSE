import os
from typing import Any, Dict

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/router", tags=["router"])

ROUTER_PATH = os.getenv("ROUTER_CONFIG", "/configs/router.yaml")
_current_router_cfg: Dict[str, Any] = {}


@router.get("/backends")
def backends() -> Any:
    return _current_router_cfg.get("backends", [])


class ReloadResp(BaseModel):
    status: str
    backends: list


@router.post("/reload", response_model=ReloadResp)
def reload_router() -> Any:
    global _current_router_cfg
    try:
        with open(ROUTER_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        if not isinstance(cfg, dict) or "backends" not in cfg or not isinstance(cfg["backends"], list):
            raise ValueError("Invalid router config: missing backends")
        _current_router_cfg = cfg
        return {"status": "ok", "backends": cfg["backends"]}
    except Exception as e:
        raise HTTPException(400, f"router reload failed: {e}")


