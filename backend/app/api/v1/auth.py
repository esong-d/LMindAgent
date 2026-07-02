

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis import asyncio as aioredis

from app.api.deps import get_db_session, get_current_user, UserInfo
from app.core.errors import ConflictError, UnauthorizedError, ok
from app.core.security import generate_jwt_token, encrypt_password, verify_password
from app.db.redis_db.client import get_redis_client
from app.db.repositories.user_repository import UserRepository
from app.schemas.user import TokenOut, UserCreate, UserLogin, UserOut


router = APIRouter()


@router.post("/register", name="注册", response_model=dict)
async def register(
    payload: UserCreate, 
    db: AsyncSession = Depends(get_db_session)
):
    users = UserRepository(db)
    if await users.get_by_email(email=str(payload.email)):
        raise ConflictError("Email already registered")

    if await users.get_by_name(name=str(payload.name)):
        raise ConflictError("user already registered")

    if payload.password != payload.confirm_password:
        raise ConflictError("Passwords do not match")
    
    hash_password, salt = encrypt_password(payload.password)
    user = await users.create(
        email=str(payload.email), 
        name=payload.name, 
        password_hash=hash_password,
        salt=salt
    )

    return ok({"user": UserOut.model_validate(user).model_dump()})


@router.post("/login", name="登录", response_model=dict)
async def login(
    payload: UserLogin, 
    db: AsyncSession = Depends(get_db_session)
):
    users = UserRepository(db)

    user = await users.get_by_email(email=str(payload.email))
    if not user or not verify_password(payload.password, user.password_hash, user.salt):
        raise UnauthorizedError("Invalid credentials")
    
    token = await generate_jwt_token(user_id=user.id)

    return ok({
        "user": UserOut.model_validate(user).model_dump(), 
        "token": TokenOut(access_token=token).model_dump()
    })


@router.post("/logout", name="退出登录", response_model=dict)
async def logout(
    current_user: UserInfo = Depends(get_current_user),
    redis_client: aioredis.Redis = Depends(get_redis_client),
):
    # token加入黑名单
    await redis_client.setex(current_user.token, 60*60*24*7, "token blacklist")
    return ok()