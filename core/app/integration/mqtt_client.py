import asyncio
import json
from typing import Any, Callable, Optional

from aiomqtt import Client
from ..metrics import mqtt_publish_total, mqtt_wait_time_ms


class AsyncMqttClient:
    def __init__(
        self,
        host: str,
        port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._client_id = client_id
        self._client: Optional[Client] = None

    async def connect(self) -> None:
        self._client = Client(
            hostname=self._host,
            port=self._port,
            username=self._username,
            password=self._password,
            client_id=self._client_id,
        )
        await self._client.connect()

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.disconnect()
            self._client = None

    async def publish_json(self, topic: str, payload: Any, qos: int = 1) -> None:
        assert self._client is not None, "MQTT not connected"
        data = json.dumps(payload, separators=(",", ":"))
        await self._client.publish(topic, data.encode("utf-8"), qos=qos)
        mqtt_publish_total.labels(topic=topic).inc()

    async def wait_for_state(
        self,
        topic: str,
        match: Optional[Callable[[Any], bool]] = None,
        timeout: float = 2.0,
    ) -> Any:
        assert self._client is not None, "MQTT not connected"
        messages = self._client.filtered_messages(topic)
        await self._client.subscribe(topic, qos=1)
        async with messages as msgs:
            try:
                while True:
                    msg_task = asyncio.create_task(msgs.__anext__())
                    done, _pending = await asyncio.wait(
                        {msg_task}, timeout=timeout, return_when=asyncio.FIRST_COMPLETED
                    )
                    if not done:
                        msg_task.cancel()
                        raise asyncio.TimeoutError("Timeout waiting for state message")
                    message = msg_task.result()
                    try:
                        data = json.loads(message.payload.decode("utf-8"))
                    except json.JSONDecodeError:
                        continue
                    if match is None or match(data):
                        mqtt_wait_time_ms.labels(topic=topic).observe(0.0)
                        return data
            finally:
                await self._client.unsubscribe(topic)

    async def publish_and_wait(
        self,
        set_topic: str,
        payload: Any,
        state_topic: str,
        match: Optional[Callable[[Any], bool]] = None,
        timeout: float = 2.0,
    ) -> Any:
        await self.publish_json(set_topic, payload)
        return await self.wait_for_state(state_topic, match=match, timeout=timeout)

    async def publish_without_wait(self, topic: str, payload: Any) -> None:
        await self.publish_json(topic, payload)


