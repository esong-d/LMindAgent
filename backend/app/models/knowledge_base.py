

from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseMUUID


class KnowledgeBase(BaseMUUID):
    __tablename__ = "knowledge_bases"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "name",
            name="unique_knowledge_base_name"
        ),
        {"comment": "知识库表,存储知识库信息,关联用户"},
    )

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False, comment="关联的用户ID")
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="知识库名称")
    description: Mapped[str] = mapped_column(String(1024), default="", nullable=False, comment="知识库描述")
    settings_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False, comment="设置JSON")
