from typing import Any, Dict, Optional
from datetime import timedelta

from ..integration.mqtt_client import AsyncMqttClient
import os
import time
import aiohttp
import asyncio
from minio import Minio
from minio.error import S3Error


class SmartHomeTools:
    def __init__(self, mqtt: AsyncMqttClient, devices: Dict[str, Dict[str, Any]]):
        self._mqtt = mqtt
        self._devices = devices
        # S3 client for snapshots
        endpoint = os.getenv("SNAPSHOT_S3_ENDPOINT")
        access_key = os.getenv("SNAPSHOT_S3_ACCESS_KEY")
        secret_key = os.getenv("SNAPSHOT_S3_SECRET_KEY")
        self._snapshot_bucket = os.getenv("SNAPSHOT_S3_BUCKET", "snapshots")
        self._snapshot_source = os.getenv("SNAPSHOT_SOURCE_URL", "http://sim:8100/sim/camera/{id}/frame")
        self._s3: Optional[Minio] = None
        if endpoint and access_key and secret_key:
            # strip http:// if present for Minio client
            secure = endpoint.startswith("https://")
            clean = endpoint.replace("https://", "").replace("http://", "")
            self._s3 = Minio(clean, access_key=access_key, secret_key=secret_key, secure=secure)

    def _device(self, device_id: str) -> Dict[str, Any]:
        if device_id not in self._devices:
            raise KeyError(f"Unknown device_id: {device_id}")
        return self._devices[device_id]

    def _set_topic(self, device_id: str) -> str:
        return self._device(device_id)["topics"]["set"]

    def _state_topic(self, device_id: str) -> str:
        return self._device(device_id)["topics"]["state"]

    async def get_device_status(self, device_id: str, timeout: float = 1.0) -> Any:
        state_topic = self._state_topic(device_id)
        return await self._mqtt.wait_for_state(state_topic, timeout=timeout)

    async def control_light(
        self, device_id: str, state: bool, brightness: Optional[int] = None
    ) -> Any:
        device = self._device(device_id)
        if device.get("type") != "light":
            raise ValueError(f"Device {device_id} is not a light")

        payload: Dict[str, Any] = {
            "type": "light",
            "state": "ON" if state else "OFF",
        }
        if brightness is not None:
            payload["brightness"] = int(max(0, min(100, brightness)))

        def match(s: Dict[str, Any]) -> bool:
            if s.get("type") != "light":
                return False
            if brightness is not None and "brightness" in s:
                return s.get("state") == payload["state"] and abs(s.get("brightness", -1) - payload["brightness"]) <= 5
            return s.get("state") == payload["state"]

        return await self._mqtt.publish_and_wait(
            set_topic=self._set_topic(device_id),
            payload=payload,
            state_topic=self._state_topic(device_id),
            match=match,
        )

    async def emit_sensor(self, sensor_id: str, value: Any) -> None:
        # helper for tests/simulated sensors
        await self._mqtt.publish_without_wait(
            topic=f"home/sensor/{sensor_id}/state",
            payload={"type": "generic", "value": value},
        )

    async def lock_door(self, device_id: str) -> Any:
        device = self._device(device_id)
        if device.get("type") != "lock":
            raise ValueError(f"Device {device_id} is not a lock")

        payload = {"type": "lock", "state": "LOCKED"}

        def match(s: Dict[str, Any]) -> bool:
            return s.get("type") == "lock" and s.get("state") == "LOCKED"

        return await self._mqtt.publish_and_wait(
            set_topic=self._set_topic(device_id),
            payload=payload,
            state_topic=self._state_topic(device_id),
            match=match,
        )

    async def unlock_door(self, device_id: str) -> Any:
        device = self._device(device_id)
        if device.get("type") != "lock":
            raise ValueError(f"Device {device_id} is not a lock")

        payload = {"type": "lock", "state": "UNLOCKED"}

        def match(s: Dict[str, Any]) -> bool:
            return s.get("type") == "lock" and s.get("state") == "UNLOCKED"

        return await self._mqtt.publish_and_wait(
            set_topic=self._set_topic(device_id),
            payload=payload,
            state_topic=self._state_topic(device_id),
            match=match,
        )

    async def cover_set_position(self, device_id: str, position: int) -> Any:
        device = self._device(device_id)
        if device.get("type") != "cover":
            raise ValueError(f"Device {device_id} is not a cover")
        position = int(max(0, min(100, position)))
        payload = {"type": "cover", "position": position}

        def match(s: Dict[str, Any]) -> bool:
            return s.get("type") == "cover" and abs(int(s.get("position", -1)) - position) <= 2

        return await self._mqtt.publish_and_wait(
            set_topic=self._set_topic(device_id),
            payload=payload,
            state_topic=self._state_topic(device_id),
            match=match,
        )

    async def switch_on(self, device_id: str) -> Any:
        device = self._device(device_id)
        if device.get("type") != "switch":
            raise ValueError(f"Device {device_id} is not a switch")
        payload = {"type": "switch", "state": "ON"}

        def match(s: Dict[str, Any]) -> bool:
            return s.get("type") == "switch" and s.get("state") == "ON"

        return await self._mqtt.publish_and_wait(
            set_topic=self._set_topic(device_id),
            payload=payload,
            state_topic=self._state_topic(device_id),
            match=match,
        )

    async def switch_off(self, device_id: str) -> Any:
        device = self._device(device_id)
        if device.get("type") != "switch":
            raise ValueError(f"Device {device_id} is not a switch")
        payload = {"type": "switch", "state": "OFF"}

        def match(s: Dict[str, Any]) -> bool:
            return s.get("type") == "switch" and s.get("state") == "OFF"

        return await self._mqtt.publish_and_wait(
            set_topic=self._set_topic(device_id),
            payload=payload,
            state_topic=self._state_topic(device_id),
            match=match,
        )

    async def set_thermostat(self, device_id: str, temperature: float) -> Any:
        device = self._device(device_id)
        if device.get("type") != "thermostat":
            raise ValueError(f"Device {device_id} is not a thermostat")
        temperature = float(temperature)
        payload = {"type": "thermostat", "target": temperature}

        def match(s: Dict[str, Any]) -> bool:
            return s.get("type") == "thermostat" and abs(float(s.get("target", -9999)) - temperature) <= 0.5

        return await self._mqtt.publish_and_wait(
            set_topic=self._set_topic(device_id),
            payload=payload,
            state_topic=self._state_topic(device_id),
            match=match,
        )

    async def siren_on(self, device_id: str) -> Any:
        device = self._device(device_id)
        if device.get("type") != "siren":
            raise ValueError(f"Device {device_id} is not a siren")
        payload = {"type": "siren", "state": "ON"}

        def match(s: Dict[str, Any]) -> bool:
            return s.get("type") == "siren" and s.get("state") == "ON"

        return await self._mqtt.publish_and_wait(
            set_topic=self._set_topic(device_id),
            payload=payload,
            state_topic=self._state_topic(device_id),
            match=match,
        )

    async def siren_off(self, device_id: str) -> Any:
        device = self._device(device_id)
        if device.get("type") != "siren":
            raise ValueError(f"Device {device_id} is not a siren")
        payload = {"type": "siren", "state": "OFF"}

        def match(s: Dict[str, Any]) -> bool:
            return s.get("type") == "siren" and s.get("state") == "OFF"

        return await self._mqtt.publish_and_wait(
            set_topic=self._set_topic(device_id),
            payload=payload,
            state_topic=self._state_topic(device_id),
            match=match,
        )

    async def arm_security(self, mode: str) -> Any:
        # Security aggregate topic; devices may be virtualized
        payload = {"type": "security", "mode": mode}

        def match(s: Dict[str, Any]) -> bool:
            return s.get("type") == "security" and s.get("mode") == mode

        return await self._mqtt.publish_and_wait(
            set_topic="home/security/set",
            payload=payload,
            state_topic="home/security/state",
            match=match,
        )

    async def disarm_security(self) -> Any:
        payload = {"type": "security", "mode": "disarmed"}

        def match(s: Dict[str, Any]) -> bool:
            return s.get("type") == "security" and s.get("mode") == "disarmed"

        return await self._mqtt.publish_and_wait(
            set_topic="home/security/set",
            payload=payload,
            state_topic="home/security/state",
            match=match,
        )

    async def camera_snapshot(self, device_id: str) -> Any:
        if not self._s3:
            return {"device_id": device_id, "snapshot": None}
        url = self._snapshot_source.replace("{id}", device_id)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.read()
        ts = int(time.time())
        key = f"{device_id}/{ts}.jpg"
        # upload to S3 (MinIO)
        from io import BytesIO
        bio = BytesIO(data)
        bio.seek(0)
        self._s3.put_object(self._snapshot_bucket, key, bio, length=len(data), content_type="image/jpeg")
        # also update last.jpg for quick previews
        bio.seek(0)
        self._s3.put_object(self._snapshot_bucket, f"{device_id}/last.jpg", bio, length=len(data), content_type="image/jpeg")
        return {"bucket": self._snapshot_bucket, "key": key, "last": f"{device_id}/last.jpg"}

    async def camera_stream_info(self, device_id: str) -> Any:
        return {"device_id": device_id, "stream": None}

    async def get_sensor_data(self, sensor_id: str, timeout: float = 1.0) -> Any:
        topic = f"home/sensor/{sensor_id}/state"
        return await self._mqtt.wait_for_state(topic, timeout=timeout)

    async def analyze_snapshot(self, camera_id: str, prompt: str) -> Any:
        # Take snapshot to S3 or return URL, then run analysis if local file exists
        snap = await self.camera_snapshot(camera_id)
        # If running without S3, just return metadata
        result: Dict[str, Any] = {"snapshot": snap}
        # Optionally download last.jpg and analyze
        try:
            import tempfile, httpx, os
            from ..llm.vision import analyze_with_gemini, gv_labels, gv_objects, gv_ocr
            url = snap.get("url") or None
            if not url and self._s3:
                # presign
                url = self._s3.presigned_get_object(self._snapshot_bucket, f"{camera_id}/last.jpg", expires=300)
            if url:
                async with httpx.AsyncClient() as client:
                    r = await client.get(url)
                    r.raise_for_status()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
                        tf.write(r.content)
                        tmp = tf.name
                facts = {
                    "gv_labels": gv_labels(tmp) or [],
                    "gv_objects": gv_objects(tmp) or [],
                    "gv_ocr": gv_ocr(tmp) or "",
                }
                prompt2 = (
                    f"Факты из Cloud Vision: labels={facts['gv_labels']}, objects={facts['gv_objects']}, "
                    f"ocr={facts['gv_ocr'][:200]}...\n\n"
                    f"Инструкция: {prompt}. Кратко, по пунктам, без дисклеймеров."
                )
                text = analyze_with_gemini(tmp, prompt2)
                os.unlink(tmp)
                result["facts"] = facts
                result["analysis"] = text
        except Exception:
            pass
        return result

    async def create_automation_rule(self, rule: Dict[str, Any]) -> Any:
        raise NotImplementedError("Rules managed via API/TriggerEngine")

    async def delete_rule(self, rule_id: str) -> Any:
        raise NotImplementedError("Rules managed via API/TriggerEngine")

    async def get_snapshot_url(self, device_id: str, expires_seconds: int = 300) -> Any:
        if not self._s3:
            return {"url": None}
        key = f"{device_id}/last.jpg"
        url = self._s3.presigned_get_object(self._snapshot_bucket, key, expires=expires_seconds)
        return {"bucket": self._snapshot_bucket, "key": key, "url": url}


