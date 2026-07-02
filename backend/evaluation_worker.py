
import asyncio
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis_db.queue import RedisStreamQueue
from app.db.session import init_engine
from app.core.log import setup_logger

from app.core.log_instance import worker_logger
from app.workers.evaluation_consumer import EvaluationStreamWorker



async def main():
    setup_logger()

    async_session_maker, _engine = await init_engine()
    if async_session_maker is None:
        return
    
    queue = RedisStreamQueue(
        stream="evaluation",
        group="evaluation_worker"
    )

    worker = EvaluationStreamWorker(
        queue=queue,
        session_maker=async_session_maker,
        concurrency=5,            # 不建议太高
        claim_interval=30,
        claim_idle_ms=60000,
    )

    await worker.run()



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        worker_logger.info("Exiting...")
