

import enum
from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, Integer, String, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseMUUID


class TaskStatus(enum.Enum):
    queued = "queued"
    running = "running"
    success = "success"
    failed = "failed"
    canceled = "canceled"

class Task(BaseMUUID):
    __tablename__ = "tasks"
    __table_args__ = (
        {"comment": "任务表,存储任务信息,关联用户、知识库、文档"},
    )

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False, comment="关联的用户ID")
    knowledge_base_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("knowledge_bases.id"), index=True, nullable=True, comment="关联的知识库ID")
    document_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("documents.id"), index=True, nullable=True, comment="关联的文档ID")

    type: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="任务类型")
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), index=True, default=TaskStatus.queued, nullable=False, comment="任务状态")
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="任务进度")
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="重试次数")

    input_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False, comment="输入JSON")
    output_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False, comment="输出JSON")
    error_message: Mapped[str] = mapped_column(String(2048), default="", nullable=False, comment="错误信息")
