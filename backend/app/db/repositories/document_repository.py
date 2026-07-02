

from datetime import datetime, timezone

from sqlalchemy import func, select, update

from app.db.repositories._base import BaseRepository
from app.models.document import Document, DocumentStatus


class DocumentRepository(BaseRepository):

    async def all(self, *, user_id: int, knowledge_base_id: str | None = None) -> list[Document]:
        conditions = [
            Document.user_id == user_id,
            Document.deleted_at.is_(None),
        ]
        if knowledge_base_id:
            conditions.append(Document.knowledge_base_id == knowledge_base_id)
        stmt = (
            select(Document)
            .where(*conditions)
            .order_by(Document.created_at.desc())
        )
        res = await self.db.scalars(stmt)
        return list(res.all())
    
    async def list_by_kb(self, *, user_id: int, knowledge_base_id: str) -> list[Document]:
        stmt = (
            select(Document)
            .where(
                Document.user_id == user_id, 
                Document.knowledge_base_id == knowledge_base_id,
                Document.deleted_at.is_(None),
            )
            .order_by(Document.created_at.desc())
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def get_by_id(self, *, user_id: int, document_id: str) -> Document | None:
        stmt = (
            select(Document)
            .where(
                Document.user_id == user_id, 
                Document.id == document_id,
                Document.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        return res.first()
    
    async def get_by_filename(self, *, user_id: int, filename: str) -> Document | None:
        stmt = (
            select(Document)
            .where(
                Document.user_id == user_id, 
                Document.filename == filename,
                Document.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        return res.first()

    async def get_by_ids(self, *, user_id: int, document_ids: list[int]) -> list[Document]:
        stmt = (
            select(Document)
            .where(
                Document.user_id == user_id,
                Document.id.in_(document_ids),
                Document.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        return list(res.all())
    
    async def get_document_count(self, user_id: int, knowledge_base_id: str | None = None) -> int:
        stmt = (
            select(func.count(Document.id))
            .where(
                Document.user_id == user_id,
                Document.deleted_at.is_(None),
            )
        )
        if knowledge_base_id:
            stmt = stmt.where(Document.knowledge_base_id == knowledge_base_id)
        res = await self.db.execute(stmt)
        return res.scalars().first()
    
    async def get_document_count_group_by_kb(self, user_id: int):
        stmt = (
            select(Document.knowledge_base_id.label("knowledge_base_id"), func.count(Document.id).label("count"))
            .where(
                Document.user_id == user_id,
                Document.deleted_at.is_(None),
            )
            .group_by(Document.knowledge_base_id)
        )
        res = await self.db.execute(stmt)
        return list(res.all())
    
    async def get_recent_document(self, user_id: int, count: int = 3):
        stmt = (
            select(Document)
            .where(
                Document.user_id == user_id,
                Document.deleted_at.is_(None),
            )
            .order_by(Document.updated_at.desc())
            .limit(count)
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def create(
        self,
        *,
        user_id: int,
        knowledge_base_id: str,
        filename: str,
        original_filename: str,
        file_type: str,
        file_size: int,
        metadata_json: dict,
    ) -> Document:
        doc = Document(
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            filename=filename,
            original_filename=original_filename,
            file_type=file_type,
            file_size=file_size,
            status=DocumentStatus.pending,
            metadata_json=metadata_json,
        )
        self.add(doc)
        await self.commit()
        await self.refresh(doc)
        return doc

    async def set_status(self, *, user_id: int, document_id: str, status: str, error_message: str = "") -> Document | None:
        stmt = (
            update(Document)
            .where(
                Document.user_id == user_id,
                Document.id == document_id,
            )
            .values(status=status)
        )
        if error_message:
            stmt = stmt.values(error_message=error_message)
            
        await self.db.execute(stmt)
        await self.commit()
    
    async def update_processing_info(
        self, 
        user_id: int, 
        document_id: str,
        processing_started_at: datetime | None = None,
        processing_completed_at: datetime | None = None,
        retry_count: int = 0
    ):
        doc = await self.get_by_id(user_id=user_id, document_id=document_id)
        if not doc:
            return None
        if processing_started_at:
            doc.processing_started_at = processing_started_at
        
        if processing_completed_at:
            doc.processing_completed_at = processing_completed_at
        
        doc.retry_count = retry_count
        await self.commit()
        await self.refresh(doc)
        return doc

    async def delete(self, *, user_id: int, document_id: str) -> bool:
        # 软删除
        stmt = (
            update(Document)
            .where(
                Document.user_id == user_id,
                Document.id == document_id,
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.commit()
        return True
