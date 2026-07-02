from datetime import datetime, timezone

from sqlalchemy import func, select, update

from app.db.repositories._base import BaseRepository
from app.models.evaluation import EvaluationGroup


class EvaluationGroupRepository(BaseRepository):

    async def get_all_groups(self, *, user_id: int) -> list[EvaluationGroup]:
        """返回所有未删除的组"""
        stmt = (
            select(EvaluationGroup)
            .where(
                EvaluationGroup.user_id == user_id,
                EvaluationGroup.deleted_at.is_(None),
            )
            .order_by(EvaluationGroup.created_at.desc())
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def list_groups(
        self, *, user_id: int, page: int = 1, page_size: int = 10
    ) -> tuple[list[EvaluationGroup], int]:
        """分页获取测评组列表"""
        total = await self.db.scalar(
            select(func.count())
            .select_from(EvaluationGroup)
            .where(
                EvaluationGroup.user_id == user_id,
                EvaluationGroup.deleted_at.is_(None),
            )
        )
        stmt = (
            select(EvaluationGroup)
            .where(
                EvaluationGroup.user_id == user_id,
                EvaluationGroup.deleted_at.is_(None),
            )
            .order_by(EvaluationGroup.created_at.desc())
            .offset(page_size * (page - 1))
            .limit(page_size)
        )
        res = await self.db.scalars(stmt)
        return list(res.all()), total

    async def get_group_by_name(self, *, user_id: int, name: str) -> EvaluationGroup | None:
        stmt = (
            select(EvaluationGroup)
            .where(
                EvaluationGroup.user_id == user_id,
                EvaluationGroup.name == name,
                EvaluationGroup.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        return res.first()

    async def get_group_by_id(self, *, user_id: int, group_id: str) -> EvaluationGroup | None:
        stmt = (
            select(EvaluationGroup)
            .where(
                EvaluationGroup.user_id == user_id,
                EvaluationGroup.id == group_id,
                EvaluationGroup.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        return res.first()

    async def get_group_by_ids(self, *, user_id: int, group_ids: list[str]) -> list[EvaluationGroup]:
        stmt = (
            select(EvaluationGroup)
            .where(
                EvaluationGroup.user_id == user_id,
                EvaluationGroup.id.in_(group_ids),
                EvaluationGroup.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def create_group(
        self, *, user_id: int, name: str, description: str = ""
    ) -> EvaluationGroup:
        group = EvaluationGroup(user_id=user_id, name=name, description=description)
        self.add(group)
        await self.commit()
        await self.refresh(group)
        return group

    async def update_group(
        self,
        *,
        user_id: int,
        group_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> EvaluationGroup | None:
        group = await self.get_group_by_id(user_id=user_id, group_id=group_id)
        if not group:
            return None
        if name is not None:
            group.name = name
        if description is not None:
            group.description = description
        await self.commit()
        await self.refresh(group)
        return group

    async def delete_group(self, *, user_id: int, group_id: str) -> bool:
        """软删除评测组"""
        stmt = (
            update(EvaluationGroup)
            .where(
                EvaluationGroup.user_id == user_id,
                EvaluationGroup.id == group_id,
                EvaluationGroup.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self.db.execute(stmt)
        await self.commit()
        return result.rowcount > 0
