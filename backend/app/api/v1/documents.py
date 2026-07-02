

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, UserInfo
from app.core.errors import ok
from app.schemas.document import DocumentOut, DocumentUpload
from app.schemas.task import TaskOut
from app.services.document_service import DocumentService


router = APIRouter()


@router.post("/documents/upload", name="上传文档", response_model=dict)
async def upload_document(
    payload: DocumentUpload,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserInfo = Depends(get_current_user),
):
    out = await DocumentService(db).upload_document(
        user_id=current_user.id,
        payload=payload,
    )
    return ok(TaskOut.model_validate(out).model_dump())

@router.get("/documents/all", name="所有文档列表", response_model=dict)
async def list_all_documents(
    knowledge_base_id: str = Query(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserInfo = Depends(get_current_user)
):
    data = await DocumentService(db).get_document_all(user_id=current_user.id, knowledge_base_id=knowledge_base_id)
    return ok(data)


@router.get("/knowledge-bases/{kb_id}/documents", name="知识库文档列表", response_model=dict)
async def list_documents(
    kb_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    docs = await DocumentService(db).list_documents(user_id=current_user.id, knowledge_base_id=kb_id)
    return ok(docs)


@router.get("/documents/{document_id}", name="文档详情", response_model=dict)
async def get_document(
    document_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    doc = await DocumentService(db).get_document(user_id=current_user.id, document_id=document_id)
    return ok(DocumentOut.model_validate(doc).model_dump())


@router.delete("/documents/{document_id}", name="删除文档", response_model=dict)
async def delete_document(
    document_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    await DocumentService(db).delete_document(user_id=current_user.id, document_id=document_id)
    return ok({"deleted": True})


@router.post("/documents/{document_id}/reprocess", name="重新处理文档", response_model=dict)
async def reprocess_document(
    document_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserInfo = Depends(get_current_user),
):
    out = await DocumentService(db).reprocess_document(user_id=current_user.id, document_id=document_id)
    return ok({"task": TaskOut.model_validate(out["task"]).model_dump()})


@router.post("/documents/{document_id}/summarize", name="文档摘要", response_model=dict)
async def summarize_document(
    document_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    doc = await DocumentService(db).get_document(user_id=current_user.id, document_id=document_id)
    return ok({"document_id": doc.id, "summary": "not implemented"})
