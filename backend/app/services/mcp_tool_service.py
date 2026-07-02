

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, NotFoundError
from app.db.repositories.mcp_repository import McpRepository


class McpToolService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.mcp = McpRepository(db)

    async def set_tool_permission(self, *, user_id: int, tool_id: str, permission_policy: str):
        tool = await self.mcp.set_tool_permission(
            user_id=user_id, tool_id=tool_id, permission_policy=permission_policy
        )
        if not tool:
            raise NotFoundError("Tool not found")
        
        return tool

    async def call_tool(
        self,
        *,
        user_id: int,
        conversation_id: str,
        message_id: str,
        server_id: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        tools = await self.mcp.list_tools(user_id=user_id, server_id=server_id)
        tool = next((t for t in tools if t.name == tool_name), None)
        if not tool or not tool.is_enabled:
            raise NotFoundError("Tool not found")
        
        requires_approval = _requires_approval(tool.permission_policy, arguments)
        call_log = await self.mcp.create_call_log(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            server_id=server_id,
            tool_id=tool.id,
            tool_name=tool.name,
            arguments_json=arguments,
            requires_approval=requires_approval,
        )
        if requires_approval:
            return {"call_log_id": call_log.id, "status": call_log.status, "requires_approval": True}
        
        raise AppError(
            code="mcp_not_implemented", 
            message="MCP tool execution is not implemented", 
            status_code=501
        )


def _requires_approval(permission_policy: str, arguments: dict[str, Any]) -> bool:
    if permission_policy == "disabled":
        return True
    
    if permission_policy == "always_confirm":
        return True
    
    if permission_policy == "confirm_on_write":
        lowered = " ".join(map(str, arguments.values())).lower()
        risky = any(k in lowered for k in ["delete", "remove", "write", "update", "create", "post", "put", "patch"])
        return risky
    
    return False
