

import enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseMUUID

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class MessageRole(enum.Enum):
    user = 'user'
    ai = 'ai'


class Message(BaseMUUID):
    __tablename__ = "messages"
    __table_args__ = (
        {"comment": "消息表,存储会话中的消息,关联会话和用户"},
    )

    conversation_id: Mapped[str] = mapped_column(String(32), ForeignKey("conversations.id"), index=True, nullable=False, comment="关联的会话ID")
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False, comment="关联的用户ID")
    message_tools_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True, comment="关联的消息工具ID")

    parent_message_id: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="父消息ID")
    role: Mapped[str] = mapped_column(String(32), nullable=False, comment="角色")
    message_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="消息类型")
    content: Mapped[str] = mapped_column(Text, default="", nullable=False, comment="内容")

    sources_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False, comment="来源JSON")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False, comment="元数据JSON")

    conversation: Mapped['Conversation'] = relationship("Conversation", back_populates="messages")