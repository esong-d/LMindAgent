

import asyncio
import uuid
from typing import Any

from .client import get_redis_client


_RELEASE_LUA = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"


class RedisDistributedLock:
    def __init__(self, *, key: str, ttl_ms: int = 10_000, purpose: str = "default", prefix: str = "lock"):
        self.key = key
        self.ttl_ms = int(ttl_ms)
        self.prefix = prefix.strip(":")
        self.token = uuid.uuid4().hex
        self.acquired = False

    def redis_key(self) -> str:
        k = self.key.strip(":")
        if not self.prefix:
            return k
        if k == self.prefix or k.startswith(f"{self.prefix}:"):
            return k
        return f"{self.prefix}:{k}"

    async def acquire(self, *, wait_ms: int = 0, retry_ms: int = 100) -> bool:
        """
        获取锁
        :param wait_ms: 0 - immediately, negative - forever
        :param retry_ms: time to wait between retries
        :return:
        """
        deadline = None if wait_ms <= 0 else (asyncio.get_running_loop().time() + wait_ms / 1000.0)
        client = await get_redis_client()
        while True:
            ok = await client.set(self.redis_key(), self.token, nx=True, px=self.ttl_ms)
            if ok:
                self.acquired = True
                return True
            if deadline is None or asyncio.get_running_loop().time() >= deadline:
                return False
            await asyncio.sleep(max(0.0, retry_ms / 1000.0))

    async def release(self) -> bool:
        """释放锁"""
        if not self.acquired:
            return False
        client = await get_redis_client()
        out = await client.eval(_RELEASE_LUA, 1, self.redis_key(), self.token)
        self.acquired = False
        return bool(out)

    async def __aenter__(self) -> "RedisDistributedLock":
        await self.acquire()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.release()


__all__ = [
    "RedisDistributedLock",
]
