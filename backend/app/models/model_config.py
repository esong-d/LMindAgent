

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseMUUID


class ModelConfig(BaseMUUID):
    """只配置对话模型"""
    __tablename__ = "model_configs"
    __table_args__ = (
        {"comment": "模型配置表,存储模型配置信息,关联用户"},
    )

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False, comment="关联的用户ID")
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="模型名称")
    provider: Mapped[str] = mapped_column(String(64), nullable=False, comment="提供商")
    base_url: Mapped[str] = mapped_column(String(1024), nullable=False, comment="基础URL")
    api_key_encrypted: Mapped[str] = mapped_column(String(4096), default="", nullable=False, comment="加密的API密钥")
    chat_model: Mapped[str] = mapped_column(String(255), default="", nullable=False, comment="聊天模型")
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False, comment="是否为默认配置")
    status: Mapped[str] = mapped_column(String(32), default="untested", nullable=False, comment="状态")
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="最后测试时间")
    last_test_result_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False, comment="最后测试结果JSON")
