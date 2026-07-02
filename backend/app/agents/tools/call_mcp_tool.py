

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.mcp_tool_service import McpToolService


async def call_mcp_tool(
    *,
    db: AsyncSession,
    user_id: int,
    conversation_id: str,
    message_id: str,
    server_id: str,
    tool_name: str,
    arguments: dict[str, Any],
):
    return await McpToolService(db).call_tool(
        user_id=user_id,
        conversation_id=conversation_id,
        message_id=message_id,
        server_id=server_id,
        tool_name=tool_name,
        arguments=arguments,
    )
