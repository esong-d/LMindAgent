import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import asyncio

from app.db.redis_db.cache import CacheTool


async def test_cache_tool():
    print("Testing CacheTool...")
    cache = CacheTool(prefix="cache")
    await cache.set("test_key", "test_value", ex_seconds=60)

    await cache.set("user:1", {"name": "alice"}, ex_seconds=300)
    data = await cache.get("user:1")  # -> {"name": "alice"}

    async def load_user():
        return {"name": "alice", "from": "db"}

    data2 = await cache.get_or_set("user:1", load_user, ex_seconds=300)
    print("Data:", data)
    print("Data2:", data2)

async def test_lock():
    from app.db.redis_db.lock import RedisDistributedLock

    lock = RedisDistributedLock(key="ingest:kb:123", ttl_ms=10_000, prefix="lock")

    ok = await lock.acquire(wait_ms=3000, retry_ms=100)
    if not ok:
        raise Exception("busy")

    try:
        # 临界区逻辑
        ...
    finally:
        await lock.release()


async def test_queue():
    from app.db.redis_db.queue import RedisStreamQueue

    queue = RedisStreamQueue(stream="tasks", group="workers", prefix="queue")

    # await queue.add({"task": "process_document", "document_id": 1236666666})
    # await queue.add({"task": "process_document", "document_id": 4569999999})

    await queue.ensure_group()
    data = await queue.read()
    # msg_id, msg = data[0]
    print("Queue data:", data)
    # cnt = await queue.ack(*['1780331805995-0', '1780331806000-0', '1780332108545-0', '1780332108546-0'])  # 替换为实际的消息ID列表
    # print("Acked:", cnt)

    res = await queue.xautoclaim(min_idle_ms=10_000, count=100)  # 自动认领超过60秒未处理的消息
    print("Auto-claimed:", res)


async def main():
    # await test_cache_tool()
    # await test_lock()
    await test_queue()

if __name__ == "__main__":
    asyncio.run(main())
