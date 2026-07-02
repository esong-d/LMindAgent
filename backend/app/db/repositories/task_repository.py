

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update

from app.db.repositories._base import BaseRepository
from app.models.task import Task, TaskStatus


class TaskRepository(BaseRepository):
    
    async def list(
            self, *, user_id: int, page: int = 1, per_page: int = 10, status: str | None = None
        ) -> tuple[list[Task], int]:
        filter = [
            Task.user_id == int(user_id),
            Task.deleted_at.is_(None),
        ]
        if status:
            filter.append(Task.status == status)
        
        total = await self.db.scalar(
            select(func.count(Task.id))
            .where(
                *filter
            )
        )

        stmt = (
            select(Task)
            .where(
                *filter
            )
            .order_by(Task.created_at.desc())
            .offset((per_page * (page - 1)))
            .limit(per_page)
            
        )
        res = await self.db.scalars(stmt)
        return res.all(), total
    
    async def get_by_id(self, *, user_id: int, task_id: str) -> Task | None:
        stmt = (
            select(Task)
            .where(
                Task.user_id == int(user_id), 
                Task.id == task_id,
                Task.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        return res.first()

    async def create(
        self,
        *,
        user_id: int,
        knowledge_base_id: str = "",
        document_id: str = "",
        type: str,
        input_json: dict | None = None,
    ) -> Task:
        task = Task(
            user_id=user_id,
            knowledge_base_id=knowledge_base_id or None,
            document_id=document_id or None,
            type=type,
            status=TaskStatus.queued,
            progress=0,
            input_json=input_json or {},
            output_json={},
        )
        self.add(task)
        await self.db.flush()
        await self.commit()
        return task

    async def update_progress(
        self, *, user_id: int, task_id: str, status: str | None = None, 
        progress: int | None = None, retry_count: int | None = None
    ) -> Task | None:
        task = await self.get_by_id(user_id=user_id, task_id=task_id)
        if not task:
            return None
        if status is not None:
            task.status = status
        if progress is not None:
            task.progress = max(0, min(100, progress))
        if retry_count is not None:
            task.retry_count = retry_count
        
        await self.commit()
        await self.refresh(task)
        return task

    async def set_result(
        self, *, user_id: int, task_id: str, input_json: dict | None = None, output_json: dict | None = None
    ) -> Task | None:
        task = await self.get_by_id(user_id=user_id, task_id=task_id)
        if not task:
            return None
        if input_json is not None:
            task.input_json = input_json
        if output_json is not None:
            task.output_json = output_json
        
        await self.commit()
        await self.refresh(task)
        return task

    async def attempt_claim(
        self, *, user_id: int, task_id: str, stale_timeout_seconds: int = 600
    ) -> bool:
        """原子认领任务

        只有 queued 或 running 超时(stale)的任务才能被认领。
        使用 UPDATE ... WHERE 实现行级锁，保证多 worker 互斥。
        返回 True 表示认领成功, False 表示已被其他 worker 认领。
        """
        stale_threshold = datetime.now(timezone.utc) - timedelta(
            seconds=stale_timeout_seconds
        )
        result = await self.db.execute(
            update(Task)
            .where(
                Task.id == task_id,
                Task.user_id == user_id,
                Task.deleted_at.is_(None),
                (
                    (Task.status == TaskStatus.queued)
                    | (
                        (Task.status == TaskStatus.running)
                        & (Task.updated_at < stale_threshold)
                    )
                ),
            )
            .values(
                status=TaskStatus.running,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.commit()
        return result.rowcount > 0
    
    async def heartbeat(self, *, user_id: int, task_id: str) -> Task | None:
        """心跳续期 — 仅更新 updated_at，防止被其他 worker 误判为超时。
        返回 True 表示续期成功, False 表示 run 不存在或已终态。
        """
        result = await self.db.execute(
            update(Task)
            .where(
                Task.id == task_id,
                Task.deleted_at.is_(None),
                Task.status == TaskStatus.running,
            )
            .values(updated_at=datetime.now(timezone.utc))
        )
        await self.commit()
        return result.rowcount == 1

    async def set_error(self, *, user_id: int, task_id: str, error_message: str) -> Task | None:
        task = await self.get_by_id(user_id=user_id, task_id=task_id)
        if not task:
            return None
        task.error_message = error_message
        await self.commit()
        await self.refresh(task)
        return task
    
    async def delete_by_id(self, *, user_id: int, task_id: str) -> Task | None:
        task = await self.get_by_id(user_id=user_id, task_id=task_id)
        if not task:
            return None
        task.deleted_at = datetime.now(timezone.utc)
        await self.commit()
        await self.refresh(task)
        return task
    
    async def delete_by_document_id(self, *, user_id: int, document_id: str) -> None:
        await self.db.execute(
            update(Task)
            .where(
                Task.user_id == user_id,
                Task.document_id == document_id,
                Task.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        await self.commit()
