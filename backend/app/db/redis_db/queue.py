import uuid
from typing import Any

import redis.asyncio as aioredis
from redis.exceptions import ResponseError

from app.db.redis_db.client import get_redis_client
from app.db.redis_db.serializer import dumps_json, loads_json


class RedisStreamQueue:
    """Redis流队列

    stream: 流名称
    group: 消费组名称
    consumer: 消费者名称
    prefix: 前缀
    """

    def __init__(
        self,
        *,
        stream: str,
        group: str = "workers",
        consumer: str | None = None,
        prefix: str = "queue",
    ):
        self.stream = stream
        self.group = group
        self.consumer = consumer or f"{uuid.uuid4().hex[:8]}"
        self.prefix = prefix.strip(":")

    def key(self) -> str:
        """队列key"""
        if not self.prefix:
            return self.stream
        return f"{self.prefix}:{self.stream}"

    async def ensure_group(self):
        """确保消费组存在"""
        client: aioredis.Redis = await get_redis_client()

        # First, check if the group already exists to avoid the BUSYGROUP error
        try:
            groups_info = await client.xinfo_groups(self.key())
            for g in groups_info:
                name = g["name"].decode() if isinstance(g["name"], bytes) else g["name"]
                if name == self.group:
                    return  
        except ResponseError:
            pass

        # Create the group (and stream if needed)
        try:
            await client.xgroup_create(
                self.key(),
                self.group,
                id="$",
                mkstream=True,
            )
        except ResponseError as e:
            # Race condition: another worker created the group between our
            # xinfo_groups check and this xgroup_create call.
            if "BUSYGROUP" not in str(e):
                raise

    async def add(
        self,
        data: Any,
        *,
        maxlen: int | None = None,
    ) -> str:
        """添加消息到队列"""
        client: aioredis.Redis = await get_redis_client()

        msg_id = await client.xadd(
            self.key(),
            {"data": dumps_json(data)},
            maxlen=maxlen,
            approximate=True,
        )

        return str(msg_id)

    async def read(
        self,
        *,
        count: int = 10,
        block_ms: int = 5000,
    ) -> list[dict]:
        """从队列读取消消息"""
        client: aioredis.Redis = await get_redis_client()

        res = await client.xreadgroup(
            groupname=self.group,
            consumername=self.consumer,
            streams={self.key(): ">"},
            count=count,
            block=block_ms,
        )

        messages = []

        for _, entries in res or []:
            for msg_id, fields in entries:
                messages.append(
                    {
                        "id": str(msg_id),
                        "data": loads_json(fields["data"]),
                    }
                )

        return messages

    async def ack(self, *ids: str):
        """确认消息"""
        if not ids:
            return

        client: aioredis.Redis = await get_redis_client()

        await client.xack(
            self.key(),
            self.group,
            *ids,
        )

    async def claim_stale(
        self,
        *,
        min_idle_ms: int = 60000,
        count: int = 100,
    ) -> list[dict]:
        """从队列读取过期消息"""
        client: aioredis.Redis = await get_redis_client()

        next_id = "0-0"
        messages = []

        while True:
            next_id, entries, _ = await client.xautoclaim(
                name=self.key(),
                groupname=self.group,
                consumername=self.consumer,
                min_idle_time=min_idle_ms,
                start_id=next_id,
                count=count,
            )

            if not entries:
                break

            for msg_id, fields in entries:
                messages.append(
                    {
                        "id": str(msg_id),
                        "data": loads_json(fields["data"]),
                    }
                )

            if next_id == "0-0":
                break

        return messages


class RedisListQueue:
    def __init__(
        self,
        *,
        stream: str,
        prefix: str = "queue",
    ):
        """
        初始化队列参数配置
        :param stream: 队列名称, 也即Redis Stream的key
        :param group: 消息分组名称, 用于Redis Stream的消费者分组
        :param consumer: 消息消费者名称, 如果为None则自动生成一个唯一ID
        :param prefix: 队列前缀, 会自动添加到stream前面, 形成最终的Redis Stream key
        """
        self.stream = stream
        self.prefix = prefix.strip(":")

    def key(self) -> str:
        if not self.prefix:
            return self.stream
        if self.stream.startswith(f"{self.prefix}:") or self.stream == self.prefix:
            return self.stream
        return f"{self.prefix}:{self.stream}"

    async def lpush(self, data: Any):
        client: aioredis.Redis = await get_redis_client()
        return await client.lpush(self.key(), dumps_json(data))

    async def lpop(self, count: int = 1):
        client: aioredis.Redis = await get_redis_client()
        # 判断是否存在队列
        key_type = await client.type(self.key())
        if key_type == "none":
            return None

        _, data = await client.blpop(self.key(), timeout=0)

        return data if data is not None else None


__all__ = [
    "RedisStreamQueue",
    "RedisListQueue",
]
