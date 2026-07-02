

from datetime import datetime, timezone

from sqlalchemy import func, select, update

from app.db.repositories._base import BaseRepository
from app.models.note import Note


class NoteRepository(BaseRepository):
    async def list_by_kb(self, *, user_id: int, knowledge_base_id: str) -> list[Note]:
        stmt = (
            select(Note)
            .where(
                Note.user_id == user_id, 
                Note.knowledge_base_id == knowledge_base_id,
                Note.deleted_at.is_(None)
            )
            .order_by(Note.updated_at.desc())
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def get_by_id(self, *, user_id: int, note_id: str) -> Note | None:
        stmt = (
            select(Note)
            .where(
                Note.user_id == user_id, 
                Note.id == note_id,
                Note.deleted_at.is_(None))
            )
        res = await self.db.scalars(stmt)
        return res.first()
    
    async def get_note_count(
        self,
        user_id: int,
        knowledge_base_id: str | None = None
    ):
        stmt = (
            select(func.count(Note.id))
            .where(
                Note.user_id == user_id,
                Note.deleted_at.is_(None)
            )
        )
        if knowledge_base_id:
            stmt = stmt.where(Note.knowledge_base_id == knowledge_base_id)

        res = await self.db.execute(stmt)
        return res.scalars().first()
    
    async def get_note_count_by_kb(
        self,
        user_id: int,
    ):
        stmt = (
            select(Note.knowledge_base_id.label("knowledge_base_id"), func.count(Note.id).label("count"))
            .where(
                Note.user_id == user_id,
                Note.deleted_at.is_(None)
            )
            .group_by(Note.knowledge_base_id)
        )
        res = await self.db.execute(stmt)
        return list(res.all())
    
    async def get_recent_note(self, user_id: int, limit: int = 3):
        stmt = (
            select(Note)
            .where(
                Note.user_id == user_id,
                Note.deleted_at.is_(None)
            )
            .order_by(Note.updated_at.desc())
            .limit(limit)
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def create(
        self,
        *,
        user_id: int,
        knowledge_base_id: str,
        title: str,
        content: str,
        tags_json: list[str],
    ) -> Note:
        note = Note(
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            title=title,
            content=content,
            tags_json=tags_json,
        )
        self.add(note)
        await self.commit()
        await self.refresh(note)
        return note

    async def update(
        self,
        *,
        user_id: int,
        note_id: str,
        title: str | None = None,
        content: str | None = None,
        tags_json: list[str] | None = None,
    ) -> Note | None:
        note = await self.get_by_id(user_id=user_id, note_id=note_id)
        if not note:
            return None
        if title is not None:
            note.title = title
        if content is not None:
            note.content = content
        if tags_json is not None:
            note.tags_json = tags_json
        
        await self.commit()
        await self.refresh(note)
        return note

    async def delete(self, *, user_id: int, note_id: str) -> bool:
        # 软删除
        stmt = (
            update(Note)
            .where(
                Note.user_id == user_id, 
                Note.id == note_id,
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.commit()
        return True
