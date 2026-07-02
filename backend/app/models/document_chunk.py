

from typing import Any, TYPE_CHECKING
from pgvector.sqlalchemy import Vector

from sqlalchemy import JSON, Computed, ForeignKey, Index, Integer, String, Text, UniqueConstraint, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import TSVECTOR

from app.core.config import get_settings
from app.models.base import BaseMUUID
if TYPE_CHECKING:
    from app.models.document import Document


def _embedding_column():
    settings = get_settings()
    try:
        return mapped_column(Vector(settings.embedding_vector_dim), nullable=True, comment="嵌入向量")
    except Exception:
        raise RuntimeError("pgvector not configured")


class DocumentChunk(BaseMUUID):
    __tablename__ = "document_chunks"
    __table_args__ = (
        Index(
            "idx_chunk_embedding",
            "embedding",
            postgresql_using="hnsw",                           # 使用HNSW算法索引向量
            postgresql_ops={"embedding": "vector_cosine_ops"}, # cosine similarity
        ),
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunk_index",
        ),
        {"comment": "文档分块表,存储文档的分块内容,关联文档和知识库"},
    )

    document_id: Mapped[str] = mapped_column(String(32), ForeignKey("documents.id"), index=True, nullable=False, comment="关联的文档ID")
    knowledge_base_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("knowledge_bases.id"), index=True, nullable=False, comment="关联的知识库ID"
    )
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False, comment="关联的用户ID")

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, comment="分块索引")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="分块内容")
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="内容哈希值")
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="token数量")

    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="页面编号")
    section_title: Mapped[str] = mapped_column(String(255), default="", nullable=False, comment="章节标题")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False, comment="元数据JSON")
    embedding: Mapped[Any | None] = _embedding_column()

    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('simple', content)",
            persisted=True
        ),
        nullable=True,
        comment="全文检索向量"
    )

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
