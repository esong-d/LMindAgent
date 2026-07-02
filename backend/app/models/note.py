

from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseMUUID


class Note(BaseMUUID):
    __tablename__ = "notes"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_base_id",
            "title",
            name="idx_unique_note_title"
        ),
        {"comment": "笔记表,存储笔记信息,关联知识库和用户"},
    )

    knowledge_base_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("knowledge_bases.id"), index=True, nullable=False, comment="关联的知识库ID"
    )
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False, comment="关联的用户ID")

    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="标题")
    content: Mapped[str] = mapped_column(Text, default="", nullable=False, comment="内容")
    tags_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False, comment="标签JSON")
