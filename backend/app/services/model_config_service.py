

import datetime as dt
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.core.security import AESCipher
from app.db.repositories.model_config_repository import ModelConfigRepository
from app.integrations.llm_provider import LLMProvider, OpenAICompatibleLLMProvider
from app.integrations.model_config_provider import ModelConfigProvider


class ModelConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.model_configs = ModelConfigRepository(db)
        self.model_config_provider = ModelConfigProvider(db)
    
    async def all_model_configs(self, user_id: int):
        items = await self.model_configs.all(user_id=user_id)
        return [{"id": item.id, "name": item.name, "provider": item.provider} for item in items]


    async def list_model_configs(self, *, user_id: int):
        res = await self.model_configs.list_by_user(user_id=user_id)
        # 默认模型排第一个
        res = sorted(res, key=lambda x: (x.is_default, x.created_at), reverse=True)
        return res

    async def get_model_config(self, *, user_id: int, model_config_id: str):
        cfg = await self.model_configs.get_by_id(user_id=user_id, model_config_id=model_config_id)
        if not cfg:
            raise NotFoundError("Model config not found")
        
        return cfg

    async def create_model_config(self, *, user_id: int, payload: dict[str, Any]):
        api_key = payload.pop("api_key", "") or ""
        payload["api_key_encrypted"] = AESCipher().encrypt(api_key) if api_key else ""

        cfg = await self.model_configs.create(user_id=user_id, payload=payload)
        if cfg.is_default:
            await self.model_configs.set_default(user_id=user_id, model_config_id=cfg.id)

        return cfg

    async def update_model_config(self, *, user_id: int, model_config_id: str, patch: dict[str, Any]):
        if "api_key" in patch and patch["api_key"] is not None:
            api_key = patch.pop("api_key") or ""
            patch["api_key_encrypted"] = AESCipher().encrypt(api_key) if api_key else ""

        cfg = await self.model_configs.update(
            user_id=user_id, model_config_id=model_config_id, patch=patch
        )
        if not cfg:
            raise NotFoundError("Model config not found")
        
        if cfg.is_default:
            await self.model_configs.set_default(user_id=user_id, model_config_id=cfg.id)

        return cfg

    async def delete_model_config(self, *, user_id: int, model_config_id: str) -> None:
        ok = await self.model_configs.delete(user_id=user_id, model_config_id=model_config_id)
        if not ok:
            raise NotFoundError("Model config not found")

    async def set_default(self, *, user_id: int, model_config_id: str):
        cfg = await self.model_configs.set_default(user_id=user_id, model_config_id=model_config_id)
        if not cfg:
            raise NotFoundError("Model config not found")
        return cfg

    async def test_connection(self, *, user_id: int, model_config_id: str) -> dict[str, Any]:
        cfg = await self.get_model_config(user_id=user_id, model_config_id=model_config_id)
        result: dict[str, Any] = {
            "tested_at": dt.datetime.now(dt.UTC).isoformat(), 
            "base_url_host": self.settings.safe_base_url_host(cfg.base_url)
        }

        status = "available"
        error: str | None = None
        try:
            if cfg.chat_model:
                llm: LLMProvider = await self.model_config_provider.build_llm_provider(user_id=user_id, model_config_id=model_config_id)
                _ = await llm.achat([{"role": "user", "content": "ping"}])

        except Exception as e:
            status = "failed"
            error = str(e)

        if error:
            result["error"] = error[:2000]

        await self.model_configs.set_test_result(
            user_id=user_id, model_config_id=cfg.id, status=status, result=result
        )

        return {"status": status, "result": result}
