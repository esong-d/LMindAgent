

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, UserInfo
from app.core.errors import ok
from app.schemas.task import TaskOut
from app.services.task_service import TaskService


router = APIRouter(prefix="/tasks")


@router.get("", name="获取任务列表", response_model=dict)
async def get_tasks(
    page: int = 1, 
    page_size: int = 10,
    status: str = None,
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    tasks, total, page, page_size = await TaskService(db).list_tasks(user_id=current_user.id, page=page, page_size=page_size, status=status)
    data = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "list": [TaskOut.model_validate(task).model_dump() for task in tasks]
    }
    return ok(data)


@router.get("/{task_id}", name="获取任务详情", response_model=dict)
async def get_task(
    task_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    task = await TaskService(db).get_task(user_id=current_user.id, task_id=task_id)
    return ok(TaskOut.model_validate(task).model_dump())


@router.post("/{task_id}/cancel", name="取消任务", response_model=dict)
async def cancel_task(
    task_id: str, 
    db: AsyncSession = Depends(get_db_session), 
    current_user: UserInfo = Depends(get_current_user)
):
    service = TaskService(db)
    await service.cancel(current_user.id, task_id)
    return ok()
