

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ConflictError
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.db.repositories.note_repository import NoteRepository
from app.schemas.knowledge_base import KnowledgeBaseOut


class KnowledgeBaseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.kbs = KnowledgeBaseRepository(db)
        self.docs = DocumentRepository(db)
        self.notes = NoteRepository(db)

    async def list_knowledge_bases(self, *, user_id: int, page: int = 1, per_page: int = 10):
        # 知识库列表
        items, total = await self.kbs.list_by_user(user_id=user_id, page=page, per_page=per_page)
        # 统计(文档和笔记)
        doc_count_list = await self.docs.get_document_count_group_by_kb(user_id=user_id)
        doc_count_dict = {item.knowledge_base_id: item.count for item in doc_count_list}
        note_count_list = await self.notes.get_note_count_by_kb(user_id=user_id)
        note_count_dict = {item.knowledge_base_id: item.count for item in note_count_list}
        # 合并
        result = []
        for item in items:
            result.append({
                **KnowledgeBaseOut.model_validate(item).model_dump(),
                "doc_cnt": doc_count_dict.get(item.id, 0),
                "note_cnt": note_count_dict.get(item.id, 0)
            })
        return result, total
    
    async def get_all_knowledge_bases(self, *, user_id: int):
        return await self.kbs.list_all(user_id=user_id)

    async def get_knowledge_base(self, *, user_id: int, knowledge_base_id: str):
        kb = await self.kbs.get_by_id(user_id=user_id, knowledge_base_id=knowledge_base_id)
        if not kb:
            raise NotFoundError("Knowledge base not found")
        return kb

    async def create_knowledge_base(
        self, *, 
        user_id: int, 
        name: str, 
        description: str, 
        settings_json: dict
    ):
        if await self.kbs.get_by_name(user_id=user_id, name=name):
            raise ConflictError("Knowledge base already exists")
        
        return await self.kbs.create(
            user_id=user_id, 
            name=name, 
            description=description, 
            settings_json=settings_json
        )

    async def update_knowledge_base(
        self,
        *,
        user_id: int,
        knowledge_base_id: str,
        name: str | None = None,
        description: str | None = None,
        settings_json: dict | None = None,
    ):
        kb = await self.kbs.update(
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            name=name,
            description=description,
            settings_json=settings_json,
        )
        if not kb:
            raise NotFoundError("Knowledge base not found")
        return kb

    async def delete_knowledge_base(self, *, user_id: int, knowledge_base_id: str) -> None:
        ok = await self.kbs.delete(user_id=user_id, knowledge_base_id=knowledge_base_id)
        if not ok:
            raise NotFoundError("Knowledge base not found")
