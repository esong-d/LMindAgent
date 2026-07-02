

from datetime import datetime, timezone

from sqlalchemy import select, update

from app.db.repositories._base import BaseRepository
from app.models.user import User


class UserRepository(BaseRepository):
    async def get_by_id(self, *, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def get_by_email(self, *, email: str) -> User | None:
        stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def get_by_name(self, *, name: str) -> User | None:
        stmt = select(User).where(User.name == name, User.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def create(self, *, email: str, name: str, password_hash: str, salt: str) -> User:
        user = User(email=email, name=name, password_hash=password_hash, salt=salt)
        self.add(user)
        await self.commit()
        await self.refresh(user)
        return user
    
    async def delete(self, *, user_id: int):
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.commit()
        return True
