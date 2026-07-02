

from datetime import datetime, timezone

from sqlalchemy import select, update

from app.db.repositories._base import BaseRepository
from app.models.conversation import Conversation


class ConversationRepository(BaseRepository):
    async def list_by_user(
        self, 
        user_id: int, 
        knowledge_base_id: str | None = None
    ) -> list[Conversation]:
        stmt = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.deleted_at.is_(None),
        )
        if knowledge_base_id:
            stmt = stmt.where(
                Conversation.knowledge_base_id == knowledge_base_id
            )
        stmt = stmt.order_by(Conversation.updated_at.desc())
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def get_by_id(
        self, 
        user_id: int, 
        conversation_id: str,
        knowledge_base_id: str | None = None
    ) -> Conversation | None:
        stmt = (
            select(Conversation)
            .where(
                Conversation.user_id == user_id, 
                Conversation.id == conversation_id,
                Conversation.deleted_at.is_(None),
            )
        )
        if knowledge_base_id:
            stmt = stmt.where(
                Conversation.knowledge_base_id == knowledge_base_id
            )
        res = await self.db.scalars(stmt)
        return res.first()

    async def create(
        self, 
        user_id: int,
        title: str,
        knowledge_base_id: str | None = None, 
    ) -> Conversation:
        conv = Conversation(
            user_id=user_id, knowledge_base_id=knowledge_base_id, title=title
        )
        self.add(conv)
        await self.commit()
        await self.refresh(conv)
        return conv

    async def delete(
        self, 
        user_id: int, 
        conversation_id: str
    ) -> bool:
        # 软删除
        stmt = (
            update(Conversation)
            .where(
                Conversation.user_id == user_id, 
                Conversation.id == conversation_id,
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.commit()
        return True
