
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Integer, JSON, String

from app.models.base import BaseMUUID


class MessageTools(BaseMUUID):
    __tablename__ = "message_tools"
    __table_args__ = {
        "comment": "消息工具表,存储消息中使用的工具信息,关联消息"
    },

    message_id: Mapped[str] = mapped_column(String(32), ForeignKey("messages.id"), index=True, nullable=False, comment="关联的消息ID")
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="工具名称")
    tool_args: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False, comment="工具参数")
    tool_result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False, comment="工具结果")
    status: Mapped[str] = mapped_column(String(32), index=True, default="pending", nullable=False, comment="状态")
    latency: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="延迟")