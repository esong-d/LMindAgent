

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, UserInfo
from app.core.errors import ok
from app.db.repositories.mcp_repository import McpRepository
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseOut,
    KnowledgeBaseUpdate,
)
from app.api.deps import UserInfo
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.model_config_service import ModelConfigService


router = APIRouter()


@router.post("/knowledge-bases", name="创建知识库", response_model=dict)
async def create_kb(
    payload: KnowledgeBaseCreate, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    kb = await KnowledgeBaseService(db).create_knowledge_base(
        user_id=current_user.id, 
        name=payload.name, 
        description=payload.description, 
        settings_json=payload.settings_json
    )
    return ok(KnowledgeBaseOut.model_validate(kb).model_dump())

@router.get("/knowledge-bases/all", name="所有知识库", response_model=dict)
async def list_all_kb(
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    items = await KnowledgeBaseService(db).get_all_knowledge_bases(user_id=current_user.id)
    return ok([KnowledgeBaseOut.model_validate(x).model_dump() for x in items])

@router.get("/knowledge-bases", name="知识库列表", response_model=dict)
async def list_kb(
    page: int = 1,
    per_page: int = 10,
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    items, total = await KnowledgeBaseService(db).list_knowledge_bases(user_id=current_user.id, page=page, per_page=per_page)
    if not items:
        return ok({"list": [], "total": total, "page": page, "per_page": per_page})
    return ok({
        "list": items, 
        "total": total, 
        "page": page, 
        "per_page": per_page
    })


@router.get("/knowledge-bases/{kb_id}", name="知识库详情", response_model=dict)
async def get_kb(
    kb_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    kb = await KnowledgeBaseService(db).get_knowledge_base(user_id=current_user.id, knowledge_base_id=kb_id)
    return ok(KnowledgeBaseOut.model_validate(kb).model_dump())


@router.post("/knowledge-bases/{kb_id}", name="更新知识库", response_model=dict)
async def update_kb(
    kb_id: str,
    payload: KnowledgeBaseUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserInfo = Depends(get_current_user),
):
    kb = await KnowledgeBaseService(db).update_knowledge_base(
        user_id=current_user.id,
        knowledge_base_id=kb_id,
        name=payload.name,
        description=payload.description,
        settings_json=payload.settings_json,
    )
    return ok(KnowledgeBaseOut.model_validate(kb).model_dump())


@router.delete("/knowledge-bases/{kb_id}", name="删除知识库", response_model=dict)
async def delete_kb(
    kb_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    await KnowledgeBaseService(db).delete_knowledge_base(user_id=current_user.id, knowledge_base_id=kb_id)
    return ok({"deleted": True})


class McpServerBindingsUpdate(BaseModel):
    server_ids: list[str]


@router.get("/knowledge-bases/{kb_id}/mcp-servers", name="知识库mcp信息", response_model=dict)
async def list_kb_mcp_servers(
    kb_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    repo = McpRepository(db)
    bindings = await repo.list_bindings_for_kb(user_id=current_user.id, knowledge_base_id=kb_id)
    return ok({"knowledge_base_id": kb_id, "server_ids": [b.mcp_server_id for b in bindings]})


@router.post("/knowledge-bases/{kb_id}/mcp-servers", name="知识库MCP更新", response_model=dict)
async def update_kb_mcp_servers(
    kb_id: str,
    payload: McpServerBindingsUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserInfo = Depends(get_current_user),
):
    repo = McpRepository(db)
    rows = await repo.set_kb_bindings(user_id=current_user.id, knowledge_base_id=kb_id, server_ids=payload.server_ids)
    return ok({"knowledge_base_id": kb_id, "server_ids": [r.mcp_server_id for r in rows]})
