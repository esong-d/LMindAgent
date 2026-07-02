

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.log_instance import worker_logger
from app.db.redis_db.queue import RedisStreamQueue
from app.workers.handlers.document_handle import handle_document_task



class StreamWorker:
    """Redis流消费者
    
    queue: Redis流队列

    handler: 消息处理函数

    concurrency: 并发数

    claim_interval: 过期检查间隔

    claim_idle_ms: 过期检查时间间隔

    """
    def __init__(
        self,
        *,
        queue,
        session_maker: async_sessionmaker[AsyncSession],
        concurrency: int = 5,
        claim_interval: int = 30,
        claim_idle_ms: int = 60000,
    ):
        self.queue: RedisStreamQueue = queue
        self.session_maker = session_maker

        self.claim_interval = claim_interval
        self.claim_idle_ms = claim_idle_ms

        self.semaphore = asyncio.Semaphore(concurrency)

    async def process_message(self, message: dict):
        """处理消息"""
        worker_logger.info(f"process message: {message}")
        async with self.semaphore:
            try:
                user_id = message["data"].get("user_id", "")
                task_id = message["data"].get('task_id', "")
                if not user_id and not task_id:
                    await self.queue.ack(message["id"])
                    worker_logger.info(f"ack {message['data']}, invalid message: {message}")
                    return
                
                res = await handle_document_task(user_id=user_id, task_id=task_id, session_maker=self.session_maker)
                
                if not res and res is not None:
                    return
                
                await self.queue.ack(message["id"])

            except Exception:
                worker_logger.exception(f"process message failed: {message['id']}")

    async def read_loop(self):
        """读取消息循环"""
        while True:
            try:
                messages = await self.queue.read( 
                    count=10,
                    block_ms=5000,
                )
                worker_logger.info(f"read messages: {messages}")

                for message in messages:
                    asyncio.create_task(self.process_message(message))

            except Exception:
                worker_logger.exception("read_loop error")
                await asyncio.sleep(5)

    async def claim_loop(self):
        """过期检查循环"""
        while True:
            try:
                messages = await self.queue.claim_stale(
                    min_idle_ms=self.claim_idle_ms,
                )
                worker_logger.info(f"claim messages: {messages}")

                for message in messages:
                    asyncio.create_task(self.process_message(message))

            except Exception:
                worker_logger.exception("claim_loop error")

            await asyncio.sleep(self.claim_interval)

    async def run(self):
        """运行消费者"""
        worker_logger.info("stream consumer start")

        await self.queue.ensure_group()

        await asyncio.gather(
            self.read_loop(),
            self.claim_loop(),
        )