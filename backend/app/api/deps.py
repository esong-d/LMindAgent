

from dataclasses import dataclass
from typing import Any

from fastapi import Depends
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.errors import UnauthorizedError
from app.core.security import verify_jwt_token
from app.db.repositories.user_repository import UserRepository
from app.db.redis_db.client import get_redis_client
from app.db.session import get_db, get_session_local


@dataclass(frozen=True)
class UserInfo:
    id: int
    token: str


security = HTTPBearer()

def get_db_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db

def get_db_factory(session_local = Depends(get_session_local)) -> async_sessionmaker:
    return session_local


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
    redis_client: aioredis.Redis = Depends(get_redis_client),
) -> UserInfo:
    token = credentials.credentials

    # 检查 token 黑名单
    if await redis_client.exists(token):
        raise UnauthorizedError("Token has been revoked")

    payload = await verify_jwt_token(token)
    if not payload:
        raise UnauthorizedError("Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id=int(user_id))
    if not user:
        raise UnauthorizedError("User not found")

    return UserInfo(id=int(user.id), token=token)

