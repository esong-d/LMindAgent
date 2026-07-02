from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.db.repositories.chunk_repository import ChunkRepository
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.db.repositories.task_repository import TaskRepository
from app.schemas.document import DocumentOut, DocumentUpload
from app.services.task_service import TaskService
from app.storage.local_storage import get_local_storage
from app.db.redis_db.queue import RedisStreamQueue


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.queue = RedisStreamQueue(stream="doc_tasks", group="document_workers")
        self.documents = DocumentRepository(db)
        self.chunks = ChunkRepository(db)
        self.tasks_repo = TaskRepository(db)
        self.knowledge_base = KnowledgeBaseRepository(db)
        self.settings = get_settings()
        self.storage = get_local_storage()

    async def list_documents(self, user_id: int, knowledge_base_id: str):
        items = await self.documents.list_by_kb(user_id=user_id, knowledge_base_id=knowledge_base_id)
        # 分片数量
        chunk_count_list = await self.chunks.count_by_kb(user_id=user_id)
        chunk_count_dict = {item.document_id: item.count for item in chunk_count_list}
        # 合并
        result = []
        for item in items:
            result.append({
                **DocumentOut.model_validate(item).model_dump(),
                "chunk_cnt": chunk_count_dict.get(item.id, 0)
            })
        
        return result
    
    async def get_document_all(self, user_id: int, knowledge_base_id: str | None = None):
        items = await self.documents.all(user_id=user_id, knowledge_base_id=knowledge_base_id)
        return [
            {
                "id": item.id,
                "filename": item.original_filename
            }
            for item in items
        ]

    async def get_document(self, *, user_id: int, document_id: str):
        doc = await self.documents.get_by_id(user_id=user_id, document_id=document_id)
        if not doc:
            raise NotFoundError("Document not found")
        return doc

    async def upload_document(
        self,
        user_id: int,
        payload: DocumentUpload,
    ) -> dict:
        doc = await self.documents.create(
            user_id=user_id,
            knowledge_base_id=payload.knowledge_base_id,
            filename=payload.new_filename,
            original_filename=payload.original_filename,
            file_type=payload.file_type,
            file_size=payload.file_size,
            metadata_json={},
        )
        task = await self.tasks_repo.create(
            user_id=user_id,
            knowledge_base_id=payload.knowledge_base_id,
            document_id=doc.id,
            type="document_ingest",
        )
        knowledge_base = await self.knowledge_base.get_by_id(
            user_id=user_id, knowledge_base_id=payload.knowledge_base_id
        )

        # 创建任务，存储Redis队列，等待worker消费
        queue_res = await self.queue.add(
            data={"task_id": task.id, "user_id": user_id}
        )
        return {
            **task.__dict__,
            "document": {"id": doc.id, "filename": doc.original_filename},
            "knowledge_base": {"id": knowledge_base.id, "name": knowledge_base.name},
            "queue_id": queue_res,
        }

    async def delete_document(self, user_id: int, document_id: str) -> None:
        doc = await self.documents.get_by_id(user_id=user_id, document_id=document_id)
        if not doc:
            raise NotFoundError("Document not found")
        
        await self.chunks.delete_by_document(user_id=user_id, document_id=document_id)
        await self.documents.delete(user_id=user_id, document_id=document_id)
        # 删除任务
        await self.tasks_repo.delete_by_document_id(user_id=user_id, document_id=document_id)

    async def reprocess_document(self, user_id: int, document_id: str) -> dict:
        doc = await self.get_document(user_id=user_id, document_id=document_id)
        task = await self.tasks_repo.create(
            user_id=user_id,
            knowledge_base_id=doc.knowledge_base_id,
            document_id=doc.id,
            type="document_ingest",
            input_json={"document_id": doc.id, "reprocess": True},
        )
        queue_res = await RedisStreamQueue(stream="document_tasks").add(
            data={"task_id": task.id, "user_id": user_id}
        )
        return {"task": task, "queue_id": queue_res, "document": doc}
