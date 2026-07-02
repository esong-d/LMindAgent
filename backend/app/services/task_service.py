import json
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.db.repositories.task_repository import TaskRepository
from app.models.task import TaskStatus


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tasks = TaskRepository(db)
        self.knowledge_base = KnowledgeBaseRepository(db)
        self.document = DocumentRepository(db)

    async def create_task(
        self, 
        *, 
        user_id: int, 
        knowledge_base_id: str = "", 
        document_id: str = "", 
        type: str, 
    ):
        return await self.tasks.create(
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            type=type,
        )
    
    async def list_tasks(self, *, user_id: int, page: int, page_size: int, status: str | None = None):
        tasks_list, total = await self.tasks.list(user_id=user_id, page=page, per_page=page_size, status=status)
        knowledge_ids = [task.knowledge_base_id for task in tasks_list]
        document_ids = [task.document_id for task in tasks_list]
        knowledge_base_list = await self.knowledge_base.get_by_knowledge_ids(user_id=user_id, knowledge_ids=knowledge_ids)
        knowledge_base_dict = {kb.id: {"id": kb.id, "name": kb.name} for kb in knowledge_base_list}
        document_list = await self.document.get_by_ids(user_id=user_id, document_ids=document_ids)
        document_dict = {doc.id: {"id": doc.id, "filename": doc.original_filename} for doc in document_list}

        result = []
        for task in tasks_list:
            result.append({
                **task.__dict__,
                "knowledge_base": knowledge_base_dict.get(task.knowledge_base_id, {}),
                "document": document_dict.get(task.document_id, {})
            })

        return result, total, page, page_size

    async def get_task(self, *, user_id: int, task_id: str):
        task = await self.tasks.get_by_id(user_id=user_id, task_id=task_id)
        if not task:
            raise NotFoundError("Task not found")
        
        knowledge_base = await self.knowledge_base.get_by_id(user_id=user_id, knowledge_base_id=task.knowledge_base_id)
        document = await self.document.get_by_id(user_id=user_id, document_id=task.document_id)
            
        return {
            **task.__dict__,
            "knowledge_base": {"id": knowledge_base.id, "name": knowledge_base.name} if knowledge_base else {},
            "document": {"id": document.id, "filename": document.original_filename} if document else {}
        }

    async def claim_task(
        self, *, user_id: int, task_id: str, stale_timeout_seconds: int = 600
    ) -> bool:
        """原子认领任务，返回 True 表示认领成功"""
        return await self.tasks.attempt_claim(
            user_id=user_id,
            task_id=task_id,
            stale_timeout_seconds=stale_timeout_seconds,
        )

    async def update_progress(
        self, 
        *, 
        user_id: int, 
        task_id: str, 
        status: str | None = None, 
        progress: int | None = None,
        retry_count: int | None = None
    ):
        task = await self.tasks.update_progress(
            user_id=user_id, 
            task_id=task_id, 
            status=status, 
            progress=progress,
            retry_count=retry_count
        )
        if not task:
            raise NotFoundError("Task not found")

        return task

    async def set_result(
        self, *, user_id: int, task_id: str, input_json: dict | None = None, output_json: dict | None = None
    ):
        task = await self.tasks.set_result(
            user_id=user_id, task_id=task_id, input_json=input_json, output_json=output_json
        )
        if not task:
            raise NotFoundError("Task not found")
        
        return task

    async def set_error(self, *, user_id: int, task_id: str, error_message: str):
        task = await self.tasks.set_error(
            user_id=user_id, task_id=task_id, error_message=error_message
        )
        if not task:
            raise NotFoundError("Task not found")
        
        return task

    async def cancel(self, user_id: int, task_id: str):
        task = await self.tasks.get_by_id(user_id=user_id, task_id=task_id)
        if task.status not in (TaskStatus.queued, TaskStatus.running):
            raise ConflictError("Task is already finished or canceled")
        
        task = await self.tasks.update_progress(
            user_id=user_id, 
            task_id=task_id, 
            status="canceled", 
            progress=task.progress
        )
        return task
