

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UserInfo, get_current_user, get_db_session
from app.core.errors import ok
from app.schemas.mcp import (
    McpCallDecision,
    McpCallLogOut,
    McpServerCreate,
    McpServerOut,
    McpServerUpdate,
    McpToolOut,
    McpToolPermissionUpdate,
)
from app.services.mcp_service import McpService
from app.services.mcp_tool_service import McpToolService


router = APIRouter(prefix="/mcp")


@router.post("/servers", name="创建MCP配置", response_model=dict)
async def create_server(
    payload: McpServerCreate, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    server = await McpService(db).create_server(user_id=current_user.id, payload=payload.model_dump())
    return ok(McpServerOut.model_validate(server).model_dump())


@router.get("/servers", name="获取MCP配置列表", response_model=dict)
async def list_servers(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserInfo = Depends(get_current_user)
):
    servers = await McpService(db).list_servers(user_id=current_user.id)
    return ok([McpServerOut.model_validate(s).model_dump() for s in servers])


@router.get("/servers/{server_id}", name="获取MCP配置", response_model=dict)
async def get_server(
    server_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    server = await McpService(db).get_server(user_id=current_user.id, server_id=server_id)
    return ok(McpServerOut.model_validate(server).model_dump())


@router.post("/servers/{server_id}", name="更新MCP配置", response_model=dict)
async def patch_server(
    server_id: str,
    payload: McpServerUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserInfo = Depends(get_current_user),
):
    server = await McpService(db).update_server(
        user_id=current_user.id, server_id=server_id, patch=payload.model_dump(exclude_unset=True)
    )
    return ok(McpServerOut.model_validate(server).model_dump())


@router.delete("/servers/{server_id}", name="删除MCP配置", response_model=dict)
async def delete_server(
    server_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    await McpService(db).delete_server(user_id=current_user.id, server_id=server_id)
    return ok({"deleted": True})


@router.post("/servers/{server_id}/test", name="测试MCP连接", response_model=dict)
async def test_server(
    server_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    return ok(await McpService(db).test_connection(user_id=current_user.id, server_id=server_id))


@router.post("/servers/{server_id}/sync", name="同步MCP配置", response_model=dict)
async def sync_server(
    server_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    return ok(await McpService(db).sync_server(user_id=current_user.id, server_id=server_id))


@router.get("/servers/{server_id}/tools", name="获取MCP工具列表", response_model=dict)
async def list_tools(
    server_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    tools = await McpService(db).list_tools(user_id=current_user.id, server_id=server_id)
    return ok([McpToolOut.model_validate(t).model_dump() for t in tools])


@router.get("/servers/{server_id}/resources", name="获取MCP资源列表", response_model=dict)
async def list_resources(
    server_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    resources = await McpService(db).list_resources(user_id=current_user.id, server_id=server_id)
    return ok(resources)


@router.post("/tools/{tool_id}/permission", name="更新MCP工具权限", response_model=dict)
async def update_tool_permission(
    tool_id: str,
    payload: McpToolPermissionUpdate,
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    tool = await McpToolService(db).set_tool_permission(
        user_id=current_user.id, tool_id=tool_id, permission_policy=payload.permission_policy
    )
    return ok(McpToolOut.model_validate(tool).model_dump())


@router.get("/call-logs", name="获取MCP调用日志列表", response_model=dict)
async def list_call_logs(
    limit: int = Query(default=50, ge=1, le=200), 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    logs = await McpService(db).list_call_logs(user_id=current_user.id, limit=limit)
    return ok([McpCallLogOut.model_validate(l).model_dump() for l in logs])


@router.post("/call-logs/{call_log_id}/approve", name="审批MCP调用", response_model=dict)
async def approve_call(
    call_log_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    log = await McpService(db).approve_call(user_id=current_user.id, call_log_id=call_log_id)
    return ok(McpCallLogOut.model_validate(log).model_dump())


@router.post("/call-logs/{call_log_id}/reject", name="拒绝MCP调用", response_model=dict)
async def reject_call(
    call_log_id: str, 
    payload: McpCallDecision, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    log = await McpService(db).reject_call(user_id=current_user.id, call_log_id=call_log_id, reason=payload.reason)
    return ok(McpCallLogOut.model_validate(log).model_dump())
