from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ok
from app.api.deps import get_current_user, get_db_session, UserInfo
from app.schemas.evaluation import (
    GroupCreate,
    GroupUpdate,
    GroupOut,
    GroupAllItem,
    GroupListOut,
    QuestionCreate,
    QuestionUpdate,
    QuestionOut,
    QuestionDetailOut,
    QuestionListOut,
    TaskCreate,
    TaskOut,
    TaskListOut,
    RunOut,
    RunListOut,
    ExecuteEvaluationRequest,
    ExecuteEvaluationResponse,
    ResultOut
)
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluation")



@router.get("/groups/all", name="获取所有测评组", response_model=dict)
async def get_all_groups(
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    result = await service.get_all_groups(user_id=current_user.id)
    return ok(data=[GroupAllItem(id=g["id"], name=g["name"]) for g in result])


@router.get("/groups", name="测评组列表", response_model=dict)
async def get_groups(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    result = await service.group_list(user_id=current_user.id, page=page, page_size=page_size)
    return ok(data=GroupListOut(
        items=[GroupOut.model_validate(g) for g in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    ).model_dump())


@router.post("/groups", name="创建测评组", response_model=dict)
async def create_group(
    payload: GroupCreate,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    result = await service.create_group(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
    )
    return ok(data=GroupOut.model_validate(result).model_dump())


@router.post("/groups/{group_id}", name="更新测评组", response_model=dict)
async def update_group(
    group_id: str,
    payload: GroupUpdate,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    result = await service.update_group(
        user_id=current_user.id,
        group_id=group_id,
        name=payload.name,
        description=payload.description,
    )
    return ok(data=GroupOut.model_validate(result).model_dump())


@router.delete("/groups/{group_id}", name="删除测评组", response_model=dict)
async def delete_group(
    group_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    await service.delete_group(user_id=current_user.id, group_id=group_id)
    return ok(data={"deleted": True})



@router.get("/questions", name="测评问题列表", response_model=dict)
async def get_questions(
    group_id: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    result = await service.evaluation_question_list(
        user_id=current_user.id, page=page, page_size=page_size, group_id=group_id
    )
    return ok(data=QuestionListOut(
        items=[QuestionOut.model_validate(q) for q in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    ).model_dump())


@router.get("/questions/group/{group_id}", name="分组Id获取问题", response_model=dict)
async def get_questions_by_group_id(
    group_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    result = await service.get_questions_by_group_id(
        user_id=current_user.id,
        group_id=group_id,
    )
    return ok(data=result)


@router.get("/questions/{question_id}", name="测评问题详情", response_model=dict)
async def get_question(
    question_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    result = await service.question_detail(
        user_id=current_user.id, question_id=question_id
    )
    return ok(data=QuestionDetailOut.model_validate(result).model_dump())


@router.post("/questions", name="创建测评问题", response_model=dict)
async def create_question(
    payload: QuestionCreate,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    res = await service.create_question(
        user_id=current_user.id,
        source=payload.source,
        group_id=payload.group_id,
        question=payload.question,
        expected_answer=payload.expected_answer,
        chunk_ids=payload.chunk_ids,
        knowledge_base_id=payload.knowledge_base_id,
        document_id=payload.document_id,
        question_count=payload.question_count,
        model_config_id=payload.model_config_id,
    )
    return ok(data=res)


@router.post("/questions/{question_id}", name="更新测评问题", response_model=dict)
async def update_question(
    question_id: str,
    payload: QuestionUpdate,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    result = await service.update_question(
        user_id=current_user.id,
        question_id=question_id,
        group_id=payload.group_id,
        question=payload.question,
        expected_answer=payload.expected_answer,
        source=payload.source,
    )
    return ok(data=QuestionDetailOut(**result).model_dump())


@router.delete("/questions/{question_id}", name="删除测评问题", response_model=dict)
async def delete_question(
    question_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    await service.delete_question(user_id=current_user.id, question_id=question_id)
    return ok(data={"deleted": True})



@router.get("/tasks", name="测评任务列表", response_model=dict)
async def get_tasks(
    group_id: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    result = await service.task_list(
        user_id=current_user.id, page=page, page_size=page_size, group_id=group_id
    )
    return ok(data=TaskListOut(
        items=[TaskOut.model_validate(t) for t in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    ).model_dump())


@router.get("/tasks/{task_id}", name="测评任务详情", response_model=dict)
async def get_task(
    task_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    task = await service.task_detail(user_id=current_user.id, task_id=task_id)
    return ok(data=TaskOut.model_validate(task).model_dump())


@router.post("/tasks", name="创建测评任务", response_model=dict)
async def create_task(
    payload: TaskCreate,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    result = await service.create_task(
        user_id=current_user.id,
        name=payload.name,
        group_id=payload.group_id,
        knowledge_base_id=payload.knowledge_base_id,
        question_ids=payload.question_ids,
        model_config_id=payload.model_config_id,
    )
    return ok(data=result)


@router.delete("/tasks/{task_id}", name="删除测评任务", response_model=dict)
async def delete_task(
    task_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    await service.delete_task(user_id=current_user.id, task_id=task_id)
    return ok(data={"deleted": True})


@router.get("/runs", name="测评运行列表", response_model=dict)
async def get_runs(
    task_id: str = Query(None, description="按任务ID过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    result = await service.run_list(
        user_id=current_user.id, page=page, page_size=page_size, task_id=task_id
    )
    return ok(data=RunListOut(
        items=[RunOut.model_validate(r) for r in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    ).model_dump())


@router.get("/runs/{run_id}", name="测评运行详情", response_model=dict)
async def get_run(
    run_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    run = await service.run_detail(user_id=current_user.id, run_id=run_id)
    return ok(data=RunOut.model_validate(run).model_dump())


@router.delete("/runs/{run_id}", name="删除测评运行", response_model=dict)
async def delete_run(
    run_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    await service.delete_run(user_id=current_user.id, run_id=run_id)
    return ok(data={"deleted": True})



@router.post("/execute", name="执行测评", response_model=dict)
async def execute_evaluation(
    payload: ExecuteEvaluationRequest,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    result = await service.execute_evaluation(
        user_id=current_user.id, task_id=payload.task_id
    )
    return ok(data=ExecuteEvaluationResponse(**result).model_dump())



@router.get("/results", name="测评结果列表", response_model=dict)
async def get_evaluation_results(
    run_id: str | None = Query(default=None, description="运行ID, 不传则返回所有结果"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    result = await service.get_evaluation_result(
        user_id=current_user.id, run_id=run_id, page=page, page_size=page_size
    )
    return ok(data={
        "items": [ResultOut.model_validate(r).model_dump() for r in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
    })


@router.get("/results/{result_id}", name="测评结果详情", response_model=dict)
async def get_result_detail(
    result_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = EvaluationService(db)
    result = await service.get_result_detail(
        user_id=current_user.id, result_id=result_id
    )
    return ok(data={
        "result": ResultOut.model_validate(result["result"]).model_dump(),
        "question": QuestionOut.model_validate(result["question"]).model_dump() if result["question"] else None,
        "task_name": result["task_name"],
    })
