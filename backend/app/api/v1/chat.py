

from collections import defaultdict
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import UserInfo, get_current_user, get_db_session
from app.core.errors import ok
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.message_repository import MessageRepository
from app.db.session import get_session_local
from app.schemas.chat import ChatReq
from app.services.chat_service import ChatService


router = APIRouter()


@router.post("/chat", name="对话(同步)", response_model=dict)
async def chat(
    payload: ChatReq, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    chat_service = ChatService(db)
    out = await chat_service.chat(payload, current_user)
    return ok(out)


@router.post("/chat/stream", name="对话(流式)")
async def chat_stream(
    payload: ChatReq, 
    db: AsyncSession = Depends(get_db_session), 
    session_factory: async_sessionmaker = Depends(get_session_local),
    current_user: UserInfo = Depends(get_current_user)
):
    # gen = ChatService(db).stream_chat(
    #     user_id=current_user.id,
    #     query=payload.query,
    #     knowledge_base_id=payload.knowledge_base_id,
    #     conversation_id=payload.conversation_id,
    # )
    gen = ChatService(db).stream_graph_chat(
        session_factory=session_factory,
        user_id=current_user.id,
        query=payload.query,
        knowledge_base_id=payload.knowledge_base_id,
        conversation_id=payload.conversation_id,
    )
    return StreamingResponse(gen, media_type="text/event-stream")


@router.get("/conversations", name="会话列表", response_model=dict)
async def list_conversations(
    kb_id: str | None = None, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    items = await ConversationRepository(db).list_by_user(
        user_id=current_user.id, knowledge_base_id=kb_id
    )
    return ok([
        {
            "id": c.id, 
            "knowledge_base_id": c.knowledge_base_id, 
            "title": c.title, 
            "updated_at": c.updated_at
        } for c in items
    ])


@router.get("/conversations/{conversation_id}", name="会话消息详情", response_model=dict)
async def list_messages(
    conversation_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    items = await MessageRepository(db).list_by_conversation(
        user_id=current_user.id, conversation_id=conversation_id
    )
    document_ids = set()
    for m in items:
        if not m.sources_json:
            continue
        for doc in m.sources_json:
            if document_id := doc.get("document_id"):
                document_ids.add(document_id)
    
    messages_source_dict = {}
    if document_ids:
        sources = await DocumentRepository(db).get_by_ids(
            user_id=current_user.id, document_ids=list(document_ids)
        )
        messages_source_dict = {
            s.id: {"document_id": s.id, "original_filename": s.original_filename}
            for s in sources
        }

    message_sources = defaultdict(list)
    for m in items:
        if not m.sources_json:
            continue

        for doc in m.sources_json:
            if messages_source_dict.get(doc.get("document_id")):
                message_sources[m.id].append(
                    {**messages_source_dict.get(doc.get("document_id")), **doc}
                )

    return ok([
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "sources": message_sources.get(m.id, []),
            "created_at": m.created_at,
        } for m in items
    ])


@router.delete("/conversations/{conversation_id}", name="删除会话", response_model=dict)
async def delete_conversation(
    conversation_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    ok_deleted = await ConversationRepository(db).delete(
        user_id=current_user.id, conversation_id=conversation_id
    )
    return ok({"deleted": ok_deleted})
