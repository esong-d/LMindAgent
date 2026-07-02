import uuid
import aiofiles
from io import BufferedReader
from pathlib import Path

from app.core.config import get_settings
from app.storage.file_storage import FileStorage
from app.core.security import md5


class LocalStorage(FileStorage):
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _new_name(self) -> str:
        return uuid.uuid4().hex

    async def save_bytes(self, user_id: int, data: bytes, original_filename: str) -> tuple[str, int, str]:
        suffix = Path(original_filename).suffix
        file_id = md5(data) or self._new_name()
        new_filename = file_id + suffix
        path = self.base_dir / str(user_id) / new_filename

        # 创建目录
        path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(path, mode="wb") as f:
            await f.write(data)
        
        return len(data), new_filename, file_id

    async def open(self, storage_path: str) -> BufferedReader:
        content = ""
        async with aiofiles.open(storage_path, "rb") as f:
            content = await f.read()
        return content

    async def delete(self, storage_path: str) -> None:
        try:
            path = Path(storage_path)
            if path.exists():
                await path.unlink(missing_ok=True)
        except FileNotFoundError:
            return

def get_local_storage() -> LocalStorage:
    settings = get_settings()
    return LocalStorage(settings.storage_local_dir)
