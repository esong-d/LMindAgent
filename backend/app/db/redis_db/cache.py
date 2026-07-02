

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from .base import RedisTool


T = TypeVar("T")


class CacheTool(RedisTool):
    def __init__(self, *, prefix: str = "cache"):
        super().__init__(prefix=prefix)

    async def get(self, key: str, *, default: T | None = None) -> T | None:
        return await self.get_json(key, default=default)

    async def set(self, key: str, value: Any, *, ex_seconds: int | None = None) -> bool:
        return await self.set_json(key, value, ex_seconds=ex_seconds)

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[T]],
        *,
        ex_seconds: int | None = None,
    ) -> T:
        cached = await self.get(key)
        if cached is not None:
            return cached
        value = await factory()
        await self.set(key, value, ex_seconds=ex_seconds)
        return value


__all__ = [
    "CacheTool",
]
