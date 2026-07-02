

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log_instance import db_logger


class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def add(self, obj):
        self.db.add(obj)
        return obj

    async def commit(self) -> None:
        try:
            await self.db.commit()
        except Exception as e:
            await self.rollback()
            db_logger.error(f"Error while committing: {e}")
            raise e

    async def refresh(self, obj) -> None:
        await self.db.refresh(obj)

    async def delete(self, obj) -> None:
        self.db.delete(obj)

    async def rollback(self) -> None:
        await self.db.rollback()
    

