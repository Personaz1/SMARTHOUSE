import asyncio
import json
import os
import random
import time
from typing import Any, Dict

from aiomqtt import Client


MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))


async def handle_messages(client: Client) -> None:
    await client.subscribe("home/device/+/set", qos=1)
    await client.subscribe("home/security/set", qos=1)
    async with client.messages() as messages:
        async for msg in messages:
            topic = msg.topic.value if hasattr(msg.topic, "value") else msg.topic
            try:
                payload: Dict[str, Any] = json.loads(msg.payload.decode("utf-8"))
            except Exception:
                continue
            parts = topic.split("/")
            state_topic = None
            if parts[1] == "device":
                device_id = parts[2]
                state_topic = f"home/device/{device_id}/state"
            elif parts[1] == "security":
                state_topic = "home/security/state"

            # introduce small jitter
            await asyncio.sleep(random.uniform(0.05, 0.2))

            # random drop 2%
            if random.random() < 0.02:
                continue
            # Echo back state with ts and slight brightness variance
            if payload.get("type") == "light":
                state = {
                    "type": "light",
                    "state": payload.get("state", "OFF"),
                    "ts": time.time(),
                }
                if "brightness" in payload:
                    # quantize to nearest 5
                    b = int(payload["brightness"]) + random.randint(-3, 3)
                    b = max(0, min(100, b))
                    q = int(round(b / 5.0) * 5)
                    state["brightness"] = q
            elif payload.get("type") == "lock":
                state = {"type": "lock", "state": payload.get("state", "UNLOCKED"), "ts": time.time()}
            elif payload.get("type") == "cover":
                pos = int(payload.get("position", 0)) + random.randint(-1, 1)
                state = {"type": "cover", "position": max(0, min(100, pos)), "ts": time.time()}
            elif payload.get("type") == "switch":
                state = {"type": "switch", "state": payload.get("state", "OFF"), "ts": time.time()}
            elif payload.get("type") == "thermostat":
                t = float(payload.get("target", 20.0)) + random.uniform(-0.2, 0.2)
                state = {"type": "thermostat", "target": round(t, 1), "ts": time.time()}
            elif payload.get("type") == "siren":
                state = {"type": "siren", "state": payload.get("state", "OFF"), "ts": time.time()}
            elif payload.get("type") == "security":
                state = {"type": "security", "mode": payload.get("mode", "disarmed"), "ts": time.time()}
            else:
                state = payload
                state["ts"] = time.time()

            if state_topic:
                await asyncio.sleep(random.uniform(0.05, 0.25))
                await client.publish(state_topic, json.dumps(state).encode("utf-8"), qos=1)


async def main() -> None:
    async with Client(hostname=MQTT_HOST, port=MQTT_PORT) as client:
        await handle_messages(client)


if __name__ == "__main__":
    asyncio.run(main())


