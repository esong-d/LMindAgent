import mimetypes
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UserInfo
from app.core.config import get_settings
from app.core.errors import AppError, ForbiddenError, NotFoundError
from app.storage.local_storage import get_local_storage
from app.db.repositories.document_repository import DocumentRepository


class FileService:
    def __init__(self, db: AsyncSession):
        self.settings = get_settings()
        self.storage = get_local_storage()
        self.document_repository = DocumentRepository(db)

    async def upload_file(self, *, current_user: UserInfo, file: UploadFile) -> dict:
        if file.content_type and \
            file.content_type not in set(self.settings.allowed_upload_mime_types):
            raise AppError(
                code=400,
                message="Unsupported file type",
                status_code=400,
                detail=file.content_type,
            )

        max_bytes = int(self.settings.max_upload_mb) * 1024 * 1024
        content = await file.read()
        if len(content) > max_bytes:
            raise AppError(code=413, message="File too large", status_code=413)

        # 保存文件
        size, new_filename, file_id = await self.storage.save_bytes(
            user_id=current_user.id, data=content, original_filename=file.filename
        )

        return {
            "file_id": file_id,
            "original_filename": file.filename,
            "new_filename": new_filename,
            "file_type": file.content_type,
            "file_size": size,
            "download_url": f"{self.settings.api_prefix}/v1/files/download/{new_filename}",
        }

    async def get_download_info(self, *, current_user: UserInfo, filename: str) -> dict:
        base_dir = (Path(self.settings.storage_local_dir) / str(current_user.id)).resolve()
        path = (Path(self.settings.storage_local_dir) / str(current_user.id) / filename).resolve()
        if not path.exists():
            raise NotFoundError("File not found")
        
        if base_dir != path and base_dir not in path.parents:
            raise ForbiddenError("Forbidden")

        if not path.exists() or not path.is_file():
            raise NotFoundError("File not found")
        
        # 获取文件信息
        document = await self.document_repository.get_by_filename(
            user_id=current_user.id, filename=filename
        )

        media_type, _ = mimetypes.guess_type(str(path))
        return {
            "path": str(path),
            "media_type": media_type or "application/octet-stream",
            "filename": filename,
            "original_filename": document.original_filename if document else filename,
        }

