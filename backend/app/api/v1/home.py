from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, UserInfo
from app.core.errors import ok
from app.services.home_service import HomeService




router = APIRouter()


@router.get("/overview")
async def overview(
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    result = await HomeService(db).get_overview(current_user)
    return ok(result)
    