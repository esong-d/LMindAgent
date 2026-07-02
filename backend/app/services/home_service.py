from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UserInfo
from app.db.repositories.chunk_repository import ChunkRepository
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.note_repository import NoteRepository
from app.schemas.document import DocumentOut
from app.schemas.note import NoteOveriew


class HomeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.document_repo: DocumentRepository = DocumentRepository(db)
        self.document_chunk_repo: ChunkRepository = ChunkRepository(db)
        self.note_repo: NoteRepository = NoteRepository(db)

    async def get_overview(self, current_user: UserInfo):
        # 文档数, 最近活动文件
        document_cnt = await self.document_repo.get_document_count(current_user.id)
        recent_doc = await self.document_repo.get_recent_document(current_user.id)
        recent_doc_list = [DocumentOut.model_validate(doc).model_dump() for doc in recent_doc] if recent_doc else []
        # 分片数
        chunk_cnt = await self.document_chunk_repo.get_chunk_count(current_user.id)
        # 笔记数
        note_cnt = await self.note_repo.get_note_count(current_user.id)
        recent_note = await self.note_repo.get_recent_note(current_user.id)
        recent_note_list = [NoteOveriew.model_validate(doc).model_dump() for doc in recent_note] if recent_note else []
        
        return {
            "document_cnt": document_cnt,
            "chunk_cnt": chunk_cnt,
            "note_cnt": note_cnt,
            "recent": {
                "doc": recent_doc_list,
                "note": recent_note_list
            }
            
        }