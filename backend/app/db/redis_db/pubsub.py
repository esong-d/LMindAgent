

from collections.abc import AsyncIterator
from typing import Any

from .client import get_redis_client
from .serializer import dumps_json, loads_json


class RedisPubSub:
    def __init__(self, *, purpose: str = "default", prefix: str = "pubsub"):
        self.prefix = prefix.strip(":")

    def key(self, channel: str) -> str:
        ch = channel.strip(":")
        if not self.prefix:
            return ch
        if ch == self.prefix or ch.startswith(f"{self.prefix}:"):
            return ch
        return f"{self.prefix}:{ch}"

    async def publish(self, channel: str, message: Any) -> int:
        client = await get_redis_client()
        return int(await client.publish(self.key(channel), dumps_json(message)))

    async def listen(self, channel: str) -> AsyncIterator[Any]:
        client = await get_redis_client()
        ps = client.pubsub()
        await ps.subscribe(self.key(channel))
        try:
            async for msg in ps.listen():
                if not msg:
                    continue
                if msg.get("type") != "message":
                    continue
                data = msg.get("data")
                if data is None:
                    yield None
                else:
                    yield loads_json(data)
        finally:
            close = getattr(ps, "close", None)
            if callable(close):
                out = close()
                if hasattr(out, "__await__"):
                    await out


__all__ = [
    "RedisPubSub",
]
