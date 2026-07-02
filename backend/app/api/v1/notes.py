

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, UserInfo
from app.core.errors import ok
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate
from app.services.note_service import NoteService


router = APIRouter()


@router.post("/notes", name="创建笔记", response_model=dict)
async def create_note(
    payload: NoteCreate, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    note = await NoteService(db).create_note(
        user_id=current_user.id,
        knowledge_base_id=payload.knowledge_base_id,
        title=payload.title,
        content=payload.content,
        tags_json=payload.tags_json,
    )
    return ok(NoteOut.model_validate(note).model_dump())


@router.get("/knowledge-bases/{kb_id}/notes", name="列出知识库下的笔记", response_model=dict)
async def list_notes(
    kb_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    notes = await NoteService(db).list_notes(user_id=current_user.id, knowledge_base_id=kb_id)
    return ok([NoteOut.model_validate(n).model_dump() for n in notes])


@router.get("/notes/{note_id}", name="获取笔记详情", response_model=dict)
async def get_note(
    note_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    note = await NoteService(db).get_note(user_id=current_user.id, note_id=note_id) 
    return ok(NoteOut.model_validate(note).model_dump())


@router.post("/notes/{note_id}", name="更新笔记", response_model=dict)
async def update_note(
    note_id: str, 
    payload: NoteUpdate, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    note = await NoteService(db).update_note(
        user_id=current_user.id,
        note_id=note_id,
        title=payload.title,
        content=payload.content,
        tags_json=payload.tags_json,
    )
    return ok(NoteOut.model_validate(note).model_dump())


@router.delete("/notes/{note_id}", name="删除笔记", response_model=dict)
async def delete_note(
    note_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    await NoteService(db).delete_note(user_id=current_user.id, note_id=note_id)
    return ok({"deleted": True})
