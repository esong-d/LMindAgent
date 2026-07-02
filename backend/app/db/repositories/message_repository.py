

from datetime import datetime, timezone

from sqlalchemy import exists, select, update

from app.db.repositories._base import BaseRepository
from app.models.message import Message



class MessageRepository(BaseRepository):
    async def list_by_conversation(self, *, user_id: int, conversation_id: str) -> list[Message]:
        from app.models.conversation import Conversation

        stmt = (
            select(Message)
            .where(
                Message.user_id == user_id, 
                Message.conversation_id == conversation_id,
                Message.deleted_at.is_(None),
                exists(
                    select(1)
                    .where(
                        Conversation.id == Message.conversation_id,
                        Conversation.user_id == user_id,
                        Conversation.deleted_at.is_(None),
                    )
                )
            )
            .order_by(Message.created_at.asc())
        )
        res = await self.db.scalars(stmt)
        return list(res.all())
    
    async def get_by_conversation_id(self, *, user_id: int, conversation_id: str) -> list[Message]:
        stmt = (
            select(Message)
            .where(
                Message.user_id == user_id, 
                Message.conversation_id == conversation_id,
                Message.deleted_at.is_(None),
            )
            .order_by(Message.created_at.asc())
        )
        res = await self.db.scalars(stmt)
        return list(res.all())
    
    async def recent_message(self, *, user_id: int, conversation_id: str, limit: int = 10) -> Message | None:
        from app.models.conversation import Conversation

        stmt = (
            select(Message)
            .where(
                Message.user_id == user_id, 
                Message.conversation_id == conversation_id,
                Message.deleted_at.is_(None),
                exists(
                    select(1)
                    .where(
                        Conversation.id == Message.conversation_id,
                        Conversation.user_id == user_id,
                        Conversation.deleted_at.is_(None),
                    )
                )
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        res = await self.db.scalars(stmt)

        messages = list(res.all())
        messages.reverse()

        return messages

    async def create(
        self,
        *,
        user_id: int,
        conversation_id: str,
        role: str,
        message_type: str,
        content: str,
        sources_json: list[dict],
        metadata_json: dict,
    ) -> Message:
        msg = Message(
            user_id=user_id,
            conversation_id=conversation_id,
            role=role,
            message_type=message_type,
            content=content,
            sources_json=sources_json,
            metadata_json=metadata_json,
        )
        self.add(msg)
        await self.commit()
        await self.refresh(msg)
        return msg
    
    async def delete(self, *, user_id: int, conversation_id: str = None, message_id: str = None) -> bool:
        if not message_id:
            return False

        stmt = (
            update(Message)
            .where(
                Message.id == message_id, 
                Message.user_id == user_id, 
                Message.deleted_at.is_(None)
            )
        )
        if conversation_id:
            stmt = stmt.where(Message.conversation_id == conversation_id)

        stmt = stmt.values(deleted_at=datetime.now(timezone.utc))
        res = await self.db.execute(stmt)
        await self.commit()
        return res.rowcount > 0
