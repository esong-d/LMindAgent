

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, UserInfo

from app.core.errors import ok
from app.schemas.user import UserOut


router = APIRouter(prefix="/users")


@router.get("/me", name="获取当前用户信息", response_model=dict)
def get_me(
    current_user: UserInfo = Depends(get_current_user)
):  
    return ok(UserOut.model_validate(current_user).model_dump())
