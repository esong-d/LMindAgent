

from datetime import datetime, timezone

from sqlalchemy import func, select, update

from app.db.repositories._base import BaseRepository
from app.models.knowledge_base import KnowledgeBase


class KnowledgeBaseRepository(BaseRepository):
    async def list_by_user(self, *, user_id: int, page: int = 1, per_page: int = 10) -> list[KnowledgeBase]:
        filters = [
            KnowledgeBase.user_id == user_id,
            KnowledgeBase.deleted_at.is_(None),
        ]

        total = await self.db.scalar(
            select(func.count())
            .select_from(KnowledgeBase)
            .where(*filters)
        )

        items = (
            await self.db.scalars(
                select(KnowledgeBase)
                .where(*filters)
                .order_by(KnowledgeBase.created_at.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
        ).all()

        return list(items), total
    
    async def list_all(self, *, user_id: int) -> list[KnowledgeBase]:
        stmt = (
            select(KnowledgeBase)
            .where(
                KnowledgeBase.deleted_at.is_(None),
                KnowledgeBase.user_id == user_id,
            )
            .order_by(KnowledgeBase.created_at.asc())
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def get_by_id(self, *, user_id: int, knowledge_base_id: str) -> KnowledgeBase | None:
        stmt = (
            select(KnowledgeBase)
            .where(
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.id == knowledge_base_id,
                KnowledgeBase.deleted_at.is_(None), 
            )
        )
        res = await self.db.scalars(stmt)
        return res.first()
    
    async def get_by_knowledge_ids(self, *, user_id: int, knowledge_ids: list[str]) -> list[KnowledgeBase]:
        stmt = (
            select(KnowledgeBase)
            .where(
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.id.in_(knowledge_ids),
                KnowledgeBase.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        return list(res.all())
    
    async def get_by_name(self, *, user_id: int, name: str) -> KnowledgeBase | None:
        stmt = (
            select(KnowledgeBase)
            .where(
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.name == name,
                KnowledgeBase.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        return res.first()

    async def create(self, *, user_id: int, name: str, description: str, settings_json: dict) -> KnowledgeBase:
        kb = KnowledgeBase(
            user_id=user_id, 
            name=name, 
            description=description, 
            settings_json=settings_json
        )
        self.add(kb)
        await self.commit()
        await self.refresh(kb)
        return kb

    async def update(
        self,
        *,
        user_id: int,
        knowledge_base_id: str,
        name: str | None = None,
        description: str | None = None,
        settings_json: dict | None = None,
    ) -> KnowledgeBase | None:
        kb = await self.get_by_id(user_id=user_id, knowledge_base_id=knowledge_base_id)
        if not kb:
            return None
        if name is not None:
            kb.name = name
        if description is not None:
            kb.description = description
        if settings_json is not None:
            kb.settings_json = settings_json
        await self.commit()
        await self.refresh(kb)
        return kb

    async def delete(self, *, user_id: int, knowledge_base_id: str) -> bool:
        # 软删除
        stmt = (
            update(KnowledgeBase)
            .where(
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.id == knowledge_base_id,
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.commit()
        return True
