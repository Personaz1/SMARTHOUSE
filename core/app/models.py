from typing import Optional
from pydantic import BaseModel, Field, conint, confloat


class ControlLightReq(BaseModel):
    device_id: str
    state: bool
    brightness: Optional[conint(ge=0, le=100)] = None


class SetThermostatReq(BaseModel):
    device_id: str
    temperature: confloat(ge=5.0, le=35.0)


class DeviceIdReq(BaseModel):
    device_id: str


class CoverSetPositionReq(BaseModel):
    device_id: str
    position: conint(ge=0, le=100)


class ArmSecurityReq(BaseModel):
    mode: Optional[str] = Field(default="away", pattern="^(away|night|home)$")


class CameraSnapshotReq(BaseModel):
    camera_id: str


