

from datetime import datetime
import enum
from typing import Any, TYPE_CHECKING

from sqlalchemy import JSON, BigInteger, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseMUUID
if TYPE_CHECKING:
    from app.models.document_chunk import DocumentChunk


class DocumentStatus(enum.Enum):
    pending = "pending"
    parsing = "parsing"
    chunking = "chunking"
    embedding = "embedding"
    completed = "completed"
    failed = "failed"

class Document(BaseMUUID):
    __tablename__ = "documents"
    __table_args__ = (
        {"comment": "文档表,存储文档信息,关联知识库和用户"},
    )

    knowledge_base_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("knowledge_bases.id"), index=True, nullable=False, comment="关联的知识库ID"
    )
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False, comment="关联的用户ID")

    filename: Mapped[str] = mapped_column(String(255), nullable=False, comment="新文件名")
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False, comment="原始文件名")
    file_type: Mapped[str] = mapped_column(String(128), nullable=False, comment="文件类型")
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, comment="文件大小")

    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), index=True, default=DocumentStatus.pending, nullable=False, comment="状态")
    error_message: Mapped[str] = mapped_column(String(2048), default="", nullable=False, comment="错误信息")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False, comment="元数据JSON")

    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="处理开始时间")
    processing_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="处理完成时间")

    chunks: Mapped[list["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")