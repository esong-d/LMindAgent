import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.task_repository import TaskRepository
from app.models.document import DocumentStatus
from app.models.task import Task, TaskStatus
from app.services.ingestion_service import IngestionService
from app.core.log_instance import worker_logger
from app.core.config import get_settings

settings = get_settings()


async def handle_document_task(
    *, task_id: str, user_id: int, session_maker: async_sessionmaker[AsyncSession]
) -> bool | None:
    """处理文档任务.

    Returns:
        None:  任务正常完成, 消息应 ack
        False: 任务未完成 (已被其他 worker 认领或等待重试), 消息不 ack
    """
    worker_logger.info(f"processing document task: {task_id}")
    
    # 心跳：每 60 秒续期 updated_at
    # 防止长时间运行被其他 worker 误判为超时重认领
    _heartbeat_stop = asyncio.Event()
    _heartbeat_task: asyncio.Task | None = None

    async def _heartbeat_loop():
        while not _heartbeat_stop.is_set():
            try:
                await asyncio.sleep(60)
                async with session_maker() as s:
                    repo = TaskRepository(s)
                    ok = await repo.heartbeat(user_id=user_id, task_id=task_id)
                    if not ok:
                        worker_logger.warning(
                            f"heartbeat failed for task_id={task_id}, "
                            f"task may have been stolen or already finished"
                        )
                        break  # task 已不再属于本 worker，停止心跳
            except asyncio.CancelledError:
                break
            except Exception as e:
                worker_logger.error(f"heartbeat error: {e}")

    _heartbeat_task = asyncio.create_task(_heartbeat_loop())

    try:
        async with session_maker() as session:
            tasks_repo = TaskRepository(session)
            task = await tasks_repo.get_by_id(user_id=user_id, task_id=task_id)
            if not task:
                worker_logger.error(f"document task not found: {task_id}")
                return None

            # 已经成功或者失败或者取消
            if task.status in (TaskStatus.success, TaskStatus.failed, TaskStatus.canceled):
                worker_logger.info(f"task already finished, task_id: {task_id}, status: {task.status}")
                return None

            # 原子认领任务(queued/running 状态超时了)
            claim_task = await tasks_repo.attempt_claim(user_id=user_id, task_id=task_id)
            if not claim_task:
                worker_logger.info("task already claimed by other worker")
                return False

            await tasks_repo.update_progress(
                user_id=user_id, task_id=task_id, status=TaskStatus.running, progress=10,
            )

            document_id = task.document_id
            worker_logger.info(f"processing document: {document_id}")
            documents_repo = DocumentRepository(session)
            await documents_repo.update_processing_info(
                user_id=user_id, document_id=document_id,
                processing_started_at=datetime.now(timezone.utc),
            )

        worker_logger.info(f"ingesting document: {document_id}")
        # 文档处理
        ingestion = IngestionService()
        count = await ingestion.ingest_document(
            user_id=user_id, document_id=document_id, task_id=task_id,
            session_maker=session_maker,
        )

        worker_logger.info(f"{document_id} ingested {count} chunks")

        async with session_maker() as session:
            documents_repo = DocumentRepository(session)
            tasks_repo = TaskRepository(session)
            await documents_repo.update_processing_info(
                user_id=user_id, document_id=document_id,
                processing_completed_at=datetime.now(timezone.utc),
            )
            await tasks_repo.update_progress(
                user_id=user_id, task_id=task_id, status=TaskStatus.success, progress=100
            )

    except Exception as e:
        try:
            async with session_maker() as session:
                tasks_repo = TaskRepository(session)
                document_repo = DocumentRepository(session)
                task: Task | None = await tasks_repo.get_by_id(user_id=user_id, task_id=task_id)

                if task is None:
                    worker_logger.error(f"task not found for error handling: {task_id}")
                    return None

                if task.retry_count < settings.max_retry_times:
                    await tasks_repo.update_progress(
                        user_id=user_id, task_id=task_id, status=TaskStatus.queued,
                        retry_count=task.retry_count + 1,
                    )
                    await tasks_repo.set_error(
                        user_id=user_id, task_id=task_id,
                        error_message=f"retrying, error: {e}",
                    )
                    worker_logger.error(f"document task failed, error: {e}, retrying...")
                    return False
                else:
                    await tasks_repo.update_progress(
                        user_id=user_id, task_id=task_id, status=TaskStatus.failed,
                    )
                    await tasks_repo.set_error(
                        user_id=user_id, task_id=task_id, error_message=str(e),
                    )
                    worker_logger.error(f"document task failed, error: {e}, no more retries")

                    # 更新文档状态
                    await document_repo.set_status(
                        user_id=user_id, document_id=task.document_id,
                        status=DocumentStatus.failed, error_message=str(e),
                    )
        except Exception as e:
            worker_logger.error(f"update task failed, error: {e}")
    
    finally:
        _heartbeat_stop.set()
        if _heartbeat_task is not None:
            _heartbeat_task.cancel()
            try:
                await _heartbeat_task
            except asyncio.CancelledError:
                pass


    worker_logger.info(f"finished processing document task: {task_id}")
