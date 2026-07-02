from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UserInfo, get_current_user, get_db_session
from app.core.errors import ok
from app.services.file_service import FileService


router = APIRouter()


@router.post("/files/upload", name="上传文件", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserInfo = Depends(get_current_user),
):
    out = await FileService(db).upload_file(current_user=current_user, file=file)
    return ok(out)


@router.get("/files/download/{filename}", name="下载文件")
async def download_file(
    filename: str,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    info = await FileService(db).get_download_info(
        current_user=current_user, filename=filename
    )
    return FileResponse(
        path=info["path"],
        media_type=info["media_type"],
        filename=info.get("original_filename", info["filename"]),
        headers={
            "Content-Disposition": f'attachment; filename="{info.get("original_filename", info["filename"])}"'
        }
    )
