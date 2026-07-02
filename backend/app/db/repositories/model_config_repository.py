

import datetime as dt
from typing import Any
from datetime import datetime, timezone
from sqlalchemy import select, update

from app.db.repositories._base import BaseRepository
from app.models.model_config import ModelConfig


class ModelConfigRepository(BaseRepository):

    async def all(self, *, user_id: int) -> list[ModelConfig]:
        stmt = (
            select(ModelConfig)
            .where(
                ModelConfig.user_id == user_id, 
                ModelConfig.deleted_at.is_(None)
            )
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def list_by_user(self, *, user_id: int) -> list[ModelConfig]:
        stmt = (
            select(ModelConfig)
            .where(ModelConfig.user_id == user_id, ModelConfig.deleted_at.is_(None))
            .order_by(ModelConfig.created_at.desc())
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def get_by_id(self, *, user_id: int, model_config_id: str) -> ModelConfig | None:
        stmt = (
            select(ModelConfig)
            .where(
                ModelConfig.user_id == user_id, 
                ModelConfig.id == model_config_id,
                ModelConfig.deleted_at.is_(None)
            )
        )
        res = await self.db.scalars(stmt)
        return res.first()

    async def create(self, *, user_id: int, payload: dict[str, Any]) -> ModelConfig:
        if not await self.get_default(user_id=user_id):
            payload["is_default"] = True
        cfg = ModelConfig(user_id=user_id, **payload)
        self.add(cfg)
        await self.commit()
        await self.refresh(cfg)
        return cfg

    async def update(self, *, user_id: int, model_config_id: str, patch: dict[str, Any]) -> ModelConfig | None:
        cfg = await self.get_by_id(user_id=user_id, model_config_id=model_config_id)
        if not cfg:
            return None
        for k, v in patch.items():
            if hasattr(cfg, k) and v is not None:
                setattr(cfg, k, v)
        await self.commit()
        await self.refresh(cfg)
        return cfg

    async def delete(self, *, user_id: int, model_config_id: str) -> bool:
        # 软删除
        stmt = (
            update(ModelConfig)
            .where(
                ModelConfig.user_id == user_id, 
                ModelConfig.id == model_config_id,
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.commit()
        return True

    async def set_default(self, *, user_id: int, model_config_id: str) -> ModelConfig | None:
        cfg = await self.get_by_id(user_id=user_id, model_config_id=model_config_id)
        if not cfg:
            return None
        
        await self.db.execute(update(ModelConfig).where(ModelConfig.user_id == user_id).values(is_default=False))
        cfg.is_default = True
        await self.commit()
        await self.refresh(cfg)
        return cfg

    async def get_default(self, *, user_id: int) -> ModelConfig | None:
        stmt = (
            select(ModelConfig)
            .where(
                ModelConfig.user_id == user_id, 
                ModelConfig.is_default == True, 
                ModelConfig.deleted_at.is_(None)
            )
        )
        res = await self.db.scalars(stmt)
        return res.first()

    async def set_test_result(
        self, *, user_id: int, model_config_id: str, status: str, result: dict[str, Any]
    ) -> ModelConfig | None:
        cfg = await self.get_by_id(user_id=user_id, model_config_id=model_config_id)
        if not cfg:
            return None
        cfg.status = status
        cfg.last_tested_at = dt.datetime.now(dt.UTC)
        cfg.last_test_result_json = result
        await self.commit()
        await self.refresh(cfg)
        return cfg