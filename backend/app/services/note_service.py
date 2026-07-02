

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.repositories.note_repository import NoteRepository


class NoteService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notes = NoteRepository(db)

    async def list_notes(self, *, user_id: int, knowledge_base_id: str):
        return await self.notes.list_by_kb(user_id=user_id, knowledge_base_id=knowledge_base_id)

    async def get_note(self, *, user_id: int, note_id: str):
        note = await self.notes.get_by_id(user_id=user_id, note_id=note_id)
        if not note:
            raise NotFoundError("Note not found")
        return note

    async def create_note(
        self,
        *,
        user_id: int,
        knowledge_base_id: str,
        title: str,
        content: str,
        tags_json: list[str] | None = None,
    ):
        return await self.notes.create(
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            title=title,
            content=content,
            tags_json=tags_json or [],
        )

    async def update_note(
        self,
        *,
        user_id: int,
        note_id: str,
        title: str | None = None,
        content: str | None = None,
        tags_json: list[str] | None = None,
    ):
        note = await self.notes.update(
            user_id=user_id, note_id=note_id, title=title, content=content, tags_json=tags_json
        )
        if not note:
            raise NotFoundError("Note not found")
        
        return note

    async def delete_note(self, *, user_id: int, note_id: str) -> None:
        ok = await self.notes.delete(user_id=user_id, note_id=note_id)
        if not ok:
            raise NotFoundError("Note not found")
