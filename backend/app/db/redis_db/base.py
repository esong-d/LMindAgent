

from typing import Any, Callable, TypeVar
from redis import asyncio as aioredis

from .client import get_redis_client
from .serializer import dumps_json, loads_json


T = TypeVar("T")


class RedisTool:
    def __init__(self, *, prefix: str = "", purpose: str = "default"):
        self.prefix = prefix.strip(":")

    def key(self, *parts: str) -> str:
        clean = [p.strip(":") for p in parts if p]
        k = ":".join(clean)
        if not self.prefix:
            return k
        if not k:
            return self.prefix
        if k == self.prefix or k.startswith(f"{self.prefix}:"):
            return k
        return f"{self.prefix}:{k}"

    async def ping(self) -> bool:
        client = await get_redis_client()
        return bool(await client.ping())

    async def get_text(self, key: str, *, default: str | None = None) -> str | None:
        client: aioredis.Redis = await get_redis_client()
        v = await client.get(self.key(key))
        return default if v is None else v

    async def set_text(
        self,
        key: str,
        value: str,
        *,
        ex_seconds: int | None = None,
        nx: bool = False,
    ) -> bool:
        client: aioredis.Redis = await get_redis_client()
        out = await client.set(self.key(key), value, ex=ex_seconds, nx=nx)
        return bool(out)

    async def delete(self, *keys: str) -> int:
        client: aioredis.Redis = await get_redis_client()
        mapped = [self.key(k) for k in keys if k]
        if not mapped:
            return 0
        return int(await client.delete(*mapped))

    async def expire(self, key: str, *, ex_seconds: int) -> bool:
        client: aioredis.Redis = await get_redis_client()
        return bool(await client.expire(self.key(key), ex_seconds))

    async def ttl(self, key: str) -> int:
        client: aioredis.Redis = await get_redis_client()
        return int(await client.ttl(self.key(key)))

    async def incr(self, key: str, *, amount: int = 1) -> int:
        client: aioredis.Redis = await get_redis_client()
        return int(await client.incr(self.key(key), amount))

    async def get_json(self, key: str, *, default: T | None = None) -> T | None:
        raw = await self.get_text(key)
        if raw is None:
            return default
        return loads_json(raw)

    async def set_json(
        self,
        key: str,
        value: Any,
        *,
        ex_seconds: int | None = None,
        nx: bool = False,
        dumps: Callable[[Any], str] = dumps_json,
    ) -> bool:
        return await self.set_text(key, dumps(value), ex_seconds=ex_seconds, nx=nx)

    async def rpush_json(self, list_key: str, value: Any, *, dumps: Callable[[Any], str] = dumps_json) -> int:
        client: aioredis.Redis = await get_redis_client()
        return int(await client.rpush(self.key(list_key), dumps(value)))

    async def blpop_json(
        self,
        list_key: str,
        *,
        timeout_seconds: int = 0,
        loads: Callable[[str], Any] = loads_json,
    ) -> Any | None:
        client: aioredis.Redis = await get_redis_client()
        out = await client.blpop(self.key(list_key), timeout=timeout_seconds)
        if not out:
            return None
        _, item = out
        return loads(item)

    async def publish_json(self, channel: str, value: Any, *, dumps: Callable[[Any], str] = dumps_json) -> int:
        client: aioredis.Redis = await get_redis_client()
        return int(await client.publish(self.key(channel), dumps(value)))


__all__ = [
    "RedisTool",
]
