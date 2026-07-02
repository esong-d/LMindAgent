

from typing import TYPE_CHECKING

from sqlalchemy import JSON, BigInteger, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseMUUID

if TYPE_CHECKING:
    from app.models.message import Message


class Conversation(BaseMUUID):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("idx_user_id_title", "user_id", "title"),
        {"comment": "会话表,记录用户的每次对话,关联知识库和用户",}
    )

    knowledge_base_id: Mapped[str] = mapped_column(String(32), index=True, nullable=True, comment="关联的知识库ID")
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False, comment="关联的用户ID")
    title: Mapped[str] = mapped_column(String(255), default="", nullable=False, comment="会话标题")

    model_name: Mapped[str] = mapped_column(String(255), default="", nullable=False, comment="模型名称")
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False, comment="温度")
    system_prompt: Mapped[str] = mapped_column(Text, default="", nullable=False, comment="系统提示")
    retrieval_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False, comment="检索配置")

    messages: Mapped[list["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")