

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UserInfo, get_current_user, get_db_session
from app.core.config import get_settings
from app.core.errors import ok
from app.core.security import AESCipher
from app.models.model_config import ModelConfig
from app.schemas.model_config import ModelConfigCreate, ModelConfigOut, ModelConfigUpdate
from app.services.model_config_service import ModelConfigService


router = APIRouter()


@router.get("/model-configs/all", name="获取所有模型", response_model=dict)
async def list_all_model_configs(
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    result = await ModelConfigService(db).all_model_configs(user_id=current_user.id)
    return ok(result)


@router.post("/model-configs", name="模型配置", response_model=dict)
async def create_model_config(
    payload: ModelConfigCreate, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    cfg = await ModelConfigService(db).create_model_config(user_id=current_user.id, payload=payload.model_dump())
    return ok(_to_out(cfg))


@router.get("/model-configs", name="获取模型配置列表", response_model=dict)
async def list_model_configs(
    db: AsyncSession = Depends(get_db_session), 
    user_id: UserInfo = Depends(get_current_user)
):
    items = await ModelConfigService(db).list_model_configs(user_id=user_id.id)
    return ok([_to_out(x) for x in items])


@router.get("/model-configs/{model_config_id}", name="获取模型配置", response_model=dict)
async def get_model_config(
    model_config_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    user_id: UserInfo = Depends(get_current_user)
):
    cfg = await ModelConfigService(db).get_model_config(user_id=user_id.id, model_config_id=model_config_id)
    return ok(_to_out(cfg))


@router.post("/model-configs/{model_config_id}", name="更新模型配置", response_model=dict)
async def update_model_config(
    model_config_id: str,
    payload: ModelConfigUpdate,
    db: AsyncSession = Depends(get_db_session),
    user_id: UserInfo = Depends(get_current_user),
):
    cfg = await ModelConfigService(db).update_model_config(
        user_id=user_id.id, model_config_id=model_config_id, patch=payload.model_dump(exclude_unset=True)
    )
    return ok(_to_out(cfg))


@router.delete("/model-configs/{model_config_id}", name="删除模型配置", response_model=dict)
async def delete_model_config(
    model_config_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    user_id: UserInfo = Depends(get_current_user)
):
    await ModelConfigService(db).delete_model_config(user_id=user_id.id, model_config_id=model_config_id)
    return ok({"deleted": True})


@router.post("/model-configs/{model_config_id}/test", name="测试模型配置连接", response_model=dict)
async def test_model_config(
    model_config_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    user_id: UserInfo = Depends(get_current_user)
):
    res = await ModelConfigService(db).test_connection(user_id=user_id.id, model_config_id=model_config_id)
    return ok(res)


@router.post("/model-configs/{model_config_id}/set-default", name="设置默认模型配置", response_model=dict)
async def set_default_model_config(
    model_config_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    user_id: UserInfo = Depends(get_current_user)
):
    cfg = await ModelConfigService(db).set_default(user_id=user_id.id, model_config_id=model_config_id)
    return ok(_to_out(cfg))


def _to_out(cfg: ModelConfig) -> dict:
    settings = get_settings()
    data = ModelConfigOut.model_validate(cfg).model_dump()
    data["api_key_masked"] = settings.masked_secret(AESCipher().decrypt(cfg.api_key_encrypted)) if cfg.api_key_encrypted else ""
    return data
