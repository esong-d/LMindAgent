

from typing import Any
from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseMUUID


class McpServer(BaseMUUID):
    __tablename__ = "mcp_servers"
    __table_args__ = (
        {"comment": "MCP服务器表,存储MCP服务器信息,关联用户"},
    )

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False, comment="关联的用户ID")

    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="服务器名称")
    description: Mapped[str] = mapped_column(String(1024), default="", nullable=False, comment="服务器描述")
    transport: Mapped[str] = mapped_column(String(32), nullable=False, comment="传输方式")
    command: Mapped[str] = mapped_column(String(1024), default="", nullable=False, comment="命令")
    args_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False, comment="参数JSON")
    url: Mapped[str] = mapped_column(String(1024), default="", nullable=False, comment="URL")
    env_json_encrypted: Mapped[str] = mapped_column(Text, default="", nullable=False, comment="环境变量JSON（加密）")
    scope: Mapped[str] = mapped_column(String(32), default="global", nullable=False, comment="作用域")

    status: Mapped[str] = mapped_column(String(32), default="untested", nullable=False, comment="状态")
    is_enabled: Mapped[bool] = mapped_column(default=True, nullable=False, comment="是否启用")
    last_connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="最后连接时间")
    last_error: Mapped[str] = mapped_column(String(2048), default="", nullable=False, comment="最后错误信息")



class McpServerBinding(BaseMUUID):
    __tablename__ = "mcp_server_bindings"
    __table_args__ = (
        {"comment": "MCP服务器绑定表,存储MCP服务器和知识库、会话的绑定关系,关联MCP服务器、知识库和会话"},
    )

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False, comment="关联的用户ID")
    mcp_server_id: Mapped[str] = mapped_column(String(32), ForeignKey("mcp_servers.id"), index=True, nullable=False, comment="关联的MCP服务器ID")
    knowledge_base_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("knowledge_bases.id"), index=True, nullable=True, comment="关联的知识库ID"
    )
    conversation_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("conversations.id"), index=True, nullable=True, comment="关联的会话ID")
    is_enabled: Mapped[bool] = mapped_column(default=True, nullable=False, comment="是否启用")


class McpTool(BaseMUUID):
    __tablename__ = "mcp_tools"
    __table_args__ = (
        {"comment": "MCP工具表,存储MCP工具信息,关联MCP服务器和用户"},
    )

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False, comment="关联的用户ID")
    mcp_server_id: Mapped[str] = mapped_column(String(32), ForeignKey("mcp_servers.id"), index=True, nullable=False, comment="关联的MCP服务器ID")

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False, comment="工具名称")
    description: Mapped[str] = mapped_column(String(2048), default="", nullable=False, comment="工具描述")
    input_schema_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False, comment="输入模式JSON")
    permission_policy: Mapped[str] = mapped_column(String(32), default="auto_allow_readonly", nullable=False, comment="权限策略")
    is_enabled: Mapped[bool] = mapped_column(default=True, nullable=False, comment="是否启用")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="最后同步时间")


class McpResource(BaseMUUID):
    __tablename__ = "mcp_resources"
    __table_args__ = (
        {"comment": "MCP资源表,存储MCP资源信息,关联MCP服务器和用户"},
    )

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False, comment="关联的用户ID")
    mcp_server_id: Mapped[str] = mapped_column(String(32), ForeignKey("mcp_servers.id"), index=True, nullable=False, comment="关联的MCP服务器ID")

    uri: Mapped[str] = mapped_column(String(1024), index=True, nullable=False, comment="资源URI")
    name: Mapped[str] = mapped_column(String(255), default="", nullable=False, comment="资源名称")
    description: Mapped[str] = mapped_column(String(2048), default="", nullable=False, comment="资源描述")
    mime_type: Mapped[str] = mapped_column(String(128), default="", nullable=False, comment="MIME类型")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False, comment="元数据JSON")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="最后同步时间")


class McpCallLog(BaseMUUID):
    __tablename__ = "mcp_call_logs"
    __table_args__ = (
        {"comment": "MCP调用日志表,存储MCP调用日志信息,关联MCP服务器、工具、会话和用户"},
    )

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True, nullable=False, comment="关联的用户ID")
    conversation_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("conversations.id"), index=True, nullable=True, comment="关联的会话ID"
    )
    message_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("messages.id"), index=True, nullable=True, comment="关联的消息ID")

    mcp_server_id: Mapped[str] = mapped_column(String(32), ForeignKey("mcp_servers.id"), index=True, nullable=False, comment="关联的MCP服务器ID")
    mcp_tool_id: Mapped[str] = mapped_column(String(32), ForeignKey("mcp_tools.id"), index=True, nullable=False, comment="关联的MCP工具ID")
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="工具名称")
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False, comment="调用状态")

    arguments_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False, comment="调用参数JSON")
    result_summary: Mapped[str] = mapped_column(Text, default="", nullable=False, comment="结果摘要")
    error_message: Mapped[str] = mapped_column(Text, default="", nullable=False, comment="错误信息")
    requires_approval: Mapped[bool] = mapped_column(default=False, nullable=False, comment="是否需要审批")
    approved_by_user: Mapped[bool] = mapped_column(default=False, nullable=False, comment="是否已被用户审批")

    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="完成时间")

