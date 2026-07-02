from sqlalchemy import BIGINT, String
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from sqlalchemy import DateTime
import uuid

from app.db.base import Base
from app.utils.generate_id import gen



class BaseMID(Base):
    __abstract__ = True
    __table_args__ = {"comment": "主键表,存储主键信息"}

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, default=lambda: next(gen), index=True, comment="主键")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="删除时间")

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class BaseMUUID(Base):
    __abstract__ = True
    __table_args__ = {"comment": "主键表,存储主键信息"}
    
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex, comment="主键")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="删除时间")