

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select, update

from app.db.repositories._base import BaseRepository
from app.models.mcp import McpCallLog, McpResource, McpServer, McpServerBinding, McpTool


class McpRepository(BaseRepository):
    async def list_servers(self, *, user_id: int) -> list[McpServer]:
        stmt = (
            select(McpServer)
            .where(
                McpServer.user_id == user_id,
                McpServer.deleted_at.is_(None)
            )
            .order_by(McpServer.created_at.desc())
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def get_server(self, *, user_id: int, server_id: str) -> McpServer | None:
        stmt = (
            select(McpServer)
            .where(
                McpServer.user_id == user_id, 
                McpServer.id == server_id,
                McpServer.deleted_at.is_(None)
            )
        )
        res = await self.db.scalars(stmt)
        return res.first()

    async def create_server(
        self,
        *,
        user_id: int,
        name: str,
        description: str,
        transport: str,
        command: str,
        args_json: list[str],
        url: str,
        env_json_encrypted: str,
        scope: str,
        is_enabled: bool,
    ) -> McpServer:
        server = McpServer(
            user_id=user_id,
            name=name,
            description=description,
            transport=transport,
            command=command,
            args_json=args_json,
            url=url,
            env_json_encrypted=env_json_encrypted,
            scope=scope,
            is_enabled=is_enabled,
            status="untested",
        )
        self.add(server)
        await self.commit()
        await self.refresh(server)
        return server

    async def update_server(self, *, user_id: int, server_id: str, patch: dict[str, Any]) -> McpServer | None:
        server = await self.get_server(user_id=user_id, server_id=server_id)
        if not server:
            return None
        for k, v in patch.items():
            if hasattr(server, k) and v is not None:
                setattr(server, k, v)
        await self.commit()
        await self.refresh(server)
        return server

    async def delete_server(self, *, user_id: int, server_id: str) -> bool:
        server = await self.get_server(user_id=user_id, server_id=server_id)
        if not server:
            return False
        await self.db.execute(
            update(McpTool)
            .where(McpTool.user_id == user_id, McpTool.mcp_server_id == server_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )
        await self.db.execute(
            update(McpResource)
            .where(McpResource.user_id == user_id, McpResource.mcp_server_id == server_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )
        await self.db.execute(
            update(McpServerBinding)
            .where(McpServerBinding.user_id == user_id, McpServerBinding.mcp_server_id == server_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )
        await self.db.execute(
            update(McpCallLog)
            .where(McpCallLog.user_id == user_id, McpCallLog.mcp_server_id == server_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )
        await self.db.delete(server)
        await self.commit()
        return True

    async def list_tools(self, *, user_id: int, server_id: str) -> list[McpTool]:
        stmt = (
            select(McpTool)
            .where(
                McpTool.user_id == user_id, 
                McpTool.mcp_server_id == server_id,
                McpTool.deleted_at.is_(None)
            )
            .order_by(McpTool.name.asc())
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def upsert_tools(self, *, user_id: int, server_id: str, tools: list[dict[str, Any]]) -> list[McpTool]:
        existing = {t.name: t for t in await self.list_tools(user_id=user_id, server_id=server_id)}
        now = datetime.now(timezone.utc)
        out: list[McpTool] = []
        for t in tools:
            name = str(t.get("name", "")).strip()
            if not name:
                continue
            if name in existing:
                row = existing[name]
                row.description = str(t.get("description") or "")
                row.input_schema_json = t.get("input_schema") or {}
                row.last_synced_at = now
                out.append(row)
            else:
                row = McpTool(
                    user_id=user_id,
                    mcp_server_id=server_id,
                    name=name,
                    description=str(t.get("description") or ""),
                    input_schema_json=t.get("input_schema") or {},
                    permission_policy="auto_allow_readonly",
                    is_enabled=True,
                    last_synced_at=now,
                )
                self.add(row)
                out.append(row)
        await self.commit()
        for row in out:
            await self.refresh(row)
        return out

    async def set_tool_permission(self, *, user_id: int, tool_id: str, permission_policy: str) -> McpTool | None:
        stmt = (
            update(McpTool)
            .where(McpTool.user_id == user_id, McpTool.id == tool_id)
            .values(permission_policy=permission_policy)
        )
        await self.db.execute(stmt)
        await self.commit()
        # 执行UPDATE后，重新查询获取更新后的工具
        return await self.get_by_id(user_id=user_id, tool_id=tool_id)

    async def list_bindings_for_kb(self, *, user_id: int, knowledge_base_id: str) -> list[McpServerBinding]:
        stmt = (
            select(McpServerBinding)
            .where(
                McpServerBinding.user_id == user_id,
                McpServerBinding.knowledge_base_id == knowledge_base_id,
                McpServerBinding.deleted_at.is_(None)
            )
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def set_kb_bindings(self, *, user_id: int, knowledge_base_id: str, server_ids: list[str]) -> list[McpServerBinding]:
        await self.db.execute(
            delete(McpServerBinding)
            .where(
                McpServerBinding.user_id == user_id, 
                McpServerBinding.knowledge_base_id == knowledge_base_id
            )
        )
        bindings = [
            McpServerBinding(user_id=user_id, mcp_server_id=sid, knowledge_base_id=knowledge_base_id, is_enabled=True)
            for sid in server_ids
        ]
        self.db.add_all(bindings)
        await self.commit()
        for b in bindings:
            await self.refresh(b)
        return bindings

    async def create_call_log(
        self,
        *,
        user_id: int,
        conversation_id: str,
        message_id: str,
        server_id: str,
        tool_id: str,
        tool_name: str,
        arguments_json: dict[str, Any],
        requires_approval: bool,
    ) -> McpCallLog:
        log = McpCallLog(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            mcp_server_id=server_id,
            mcp_tool_id=tool_id,
            tool_name=tool_name,
            status="queued" if not requires_approval else "approval_required",
            arguments_json=arguments_json,
            requires_approval=requires_approval,
            approved_by_user=False,
        )
        self.add(log)
        await self.commit()
        await self.refresh(log)
        return log

    async def list_call_logs(self, *, user_id: int, limit: int = 50) -> list[McpCallLog]:
        stmt = (
            select(McpCallLog)
            .where(McpCallLog.user_id == user_id, McpCallLog.deleted_at.is_(None))
            .order_by(McpCallLog.created_at.desc())
            .limit(limit)
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def get_call_log(self, *, user_id: int, call_log_id: str) -> McpCallLog | None:
        stmt = (
            select(McpCallLog)
            .where(
                McpCallLog.user_id == user_id, 
                McpCallLog.id == call_log_id,
                McpCallLog.deleted_at.is_(None)
            )
        )
        res = await self.db.scalars(stmt)
        return res.first()

    async def approve_call(self, *, user_id: int, call_log_id: str) -> McpCallLog | None:
        log = await self.get_call_log(user_id=user_id, call_log_id=call_log_id)
        if not log:
            return None
        log.approved_by_user = True
        if log.status == "approval_required":
            log.status = "queued"
        await self.commit()
        await self.refresh(log)
        return log

    async def reject_call(self, *, user_id: int, call_log_id: str, reason: str = "") -> McpCallLog | None:
        log = await self.get_call_log(user_id=user_id, call_log_id=call_log_id)
        if not log:
            return None
        log.status = "canceled"
        log.error_message = reason
        log.completed_at = datetime.now(timezone.utc)
        await self.commit()
        await self.refresh(log)
        return log
