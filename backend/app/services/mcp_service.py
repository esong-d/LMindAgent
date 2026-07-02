

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.security import AESCipher
from app.db.repositories.mcp_repository import McpRepository


class McpService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.mcp = McpRepository(db)

    async def list_servers(self, *, user_id: int):
        return await self.mcp.list_servers(user_id=user_id)

    async def get_server(self, *, user_id: int, server_id: str):
        server = await self.mcp.get_server(user_id=user_id, server_id=server_id)
        if not server:
            raise NotFoundError("MCP server not found")
        
        return server

    async def create_server(self, *, user_id: int, payload: dict[str, Any]):
        env_json = payload.pop("env_json", {}) or {}
        env_encrypted = AESCipher.encrypt(json.dumps(env_json, ensure_ascii=False))

        return await self.mcp.create_server(
            user_id=user_id, 
            env_json_encrypted=env_encrypted, 
            **payload
        )

    async def update_server(self, *, user_id: int, server_id: str, patch: dict[str, Any]):
        if "env_json" in patch and patch["env_json"] is not None:
            env_encrypted = AESCipher.encrypt(json.dumps(patch.pop("env_json"), ensure_ascii=False))
            patch["env_json_encrypted"] = env_encrypted

        server = await self.mcp.update_server(user_id=user_id, server_id=server_id, patch=patch)
        if not server:
            raise NotFoundError("MCP server not found")
        
        return server

    async def delete_server(self, *, user_id: int, server_id: str) -> None:
        ok = await self.mcp.delete_server(user_id=user_id, server_id=server_id)
        if not ok:
            raise NotFoundError("MCP server not found")

    async def test_connection(self, *, user_id: int, server_id: str) -> dict[str, Any]:
        server = await self.get_server(user_id=user_id, server_id=server_id)
        return {
            "server_id": server.id, 
            "status": "untested", 
            "detail": "connection testing not implemented"
        }

    async def sync_server(self, *, user_id: int, server_id: str) -> dict[str, Any]:
        server = await self.get_server(user_id=user_id, server_id=server_id)
        tools = []
        upserted = await self.mcp.upsert_tools(
            user_id=user_id, server_id=server.id, tools=tools
        )
        return {"server_id": server.id, "tools_count": len(upserted)}

    async def list_tools(self, *, user_id: int, server_id: str):
        _ = await self.get_server(user_id=user_id, server_id=server_id)
        return await self.mcp.list_tools(user_id=user_id, server_id=server_id)

    async def list_resources(self, *, user_id: int, server_id: str):
        _ = await self.get_server(user_id=user_id, server_id=server_id)
        return []

    async def get_server_env_json(self, *, user_id: int, server_id: str) -> dict[str, Any]:
        server = await self.get_server(user_id=user_id, server_id=server_id)
        if not server.env_json_encrypted:
            return {}
        plaintext = AESCipher.decrypt(server.env_json_encrypted)
        return json.loads(plaintext)

    async def list_call_logs(self, *, user_id: int, limit: int = 50):
        return await self.mcp.list_call_logs(user_id=user_id, limit=limit)

    async def approve_call(self, *, user_id: int, call_log_id: str):
        log = await self.mcp.approve_call(user_id=user_id, call_log_id=call_log_id)
        if not log:
            raise NotFoundError("Call log not found")
        return log

    async def reject_call(self, *, user_id: int, call_log_id: str, reason: str = ""):
        log = await self.mcp.reject_call(
            user_id=user_id, call_log_id=call_log_id, reason=reason
        )
        if not log:
            raise NotFoundError("Call log not found")
        return log
