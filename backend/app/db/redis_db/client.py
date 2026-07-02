

import asyncio
from typing import Any
from redis import asyncio as aioredis

from app.core.config import get_settings
from app.core.log_instance import app_logger


_client: Any | None = None
_client_lock = asyncio.Lock()


async def _close_client(client: Any) -> None:
    close = getattr(client, "close", None)
    if callable(close):
        out = close()
        if asyncio.iscoroutine(out):
            await out

    pool = getattr(client, "connection_pool", None)
    disconnect = getattr(pool, "disconnect", None) if pool is not None else None
    if callable(disconnect):
        try:
            out = disconnect(inuse_connections=True)
        except TypeError:
            out = disconnect()
        if asyncio.iscoroutine(out):
            await out


async def get_redis_client() -> Any:
    global _client
    if _client is not None:
        return _client

    try:
        async with _client_lock:
            if _client is not None:
                return _client

            settings = get_settings()
            _client = aioredis.from_url(
                settings.redis_url, 
                encoding="utf-8", 
                socket_timeout=30,
                socket_connect_timeout=10,
                decode_responses=True
            )
            app_logger.info("redis 连接成功")
            return _client
    except Exception as e:
        app_logger.info(f"redis 连接失败, error: {e}")
        raise e


async def close_redis_client() -> None:
    global _client
    if _client is None:
        return
    client = _client
    _client = None
    await _close_client(client)
    app_logger.info("redis 连接关闭")


__all__ = [
    "get_redis_client",
    "close_redis_client",
]
