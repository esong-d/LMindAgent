from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select, update

from app.db.repositories._base import BaseRepository
from app.models.evaluation import (
    EvaluationTask,
    EvaluationResult,
    EvaluationResultStatus,
    EvaluationTaskType,
)


class EvaluationTaskRepository(BaseRepository):
    """测评任务 Repository"""

    async def list_tasks(
        self, *, user_id: int, page: int = 1, page_size: int = 10, group_id: str | None = None
    ) -> tuple[list[EvaluationTask], int]:
        conditions = [
            EvaluationTask.user_id == user_id,
            EvaluationTask.deleted_at.is_(None),
        ]
        if group_id:
            conditions.append(EvaluationTask.group_id == group_id)

        total = await self.db.scalar(
            select(func.count())
            .select_from(EvaluationTask)
            .where(*conditions)
        )
        stmt = (
            select(EvaluationTask)
            .where(*conditions)
            .order_by(EvaluationTask.created_at.desc())
            .offset(page_size * (page - 1))
            .limit(page_size)
        )
        res = await self.db.scalars(stmt)
        return list(res.all()), total

    async def get_task_by_id(self, *, user_id: int, task_id: str) -> EvaluationTask | None:
        stmt = (
            select(EvaluationTask)
            .where(
                EvaluationTask.user_id == user_id,
                EvaluationTask.id == task_id,
                EvaluationTask.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        return res.first()

    async def create_task(
        self,
        *,
        name: str,
        group_id: str,
        user_id: int,
        type: EvaluationTaskType,
        knowledge_base_id: str,
        total_questions: int = 0,
        question_ids: list[str] | None = None,
        config: dict | None = None,
    ) -> EvaluationTask:
        task = EvaluationTask(
            name=name,
            group_id=group_id,
            user_id=user_id,
            type=type,
            knowledge_base_id=knowledge_base_id,
            total_questions=total_questions,
            config=config or {},
            question_ids=question_ids or [],
        )
        self.add(task)
        await self.commit()
        await self.refresh(task)
        return task

    async def update_task(
        self,
        *,
        user_id: int,
        task_id: str,
        name: str | None = None,
        total_questions: int | None = None,
        question_ids: list[str] | None = None,
        config: dict | None = None,
    ) -> EvaluationTask | None:
        task = await self.get_task_by_id(user_id=user_id, task_id=task_id)
        if not task:
            return None
        if name is not None:
            task.name = name
        if total_questions is not None:
            task.total_questions = total_questions
        if question_ids is not None:
            task.question_ids = question_ids
        if config is not None:
            task.config = config
        await self.commit()
        await self.refresh(task)
        return task

    async def delete_task(self, *, user_id: int, task_id: str) -> bool:
        """软删除测评任务"""
        stmt = (
            update(EvaluationTask)
            .where(
                EvaluationTask.user_id == user_id,
                EvaluationTask.id == task_id,
                EvaluationTask.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self.db.execute(stmt)
        await self.commit()
        return result.rowcount > 0


class EvaluationResultRepository(BaseRepository):
    """测评结果 Repository"""

    async def list_results(
        self,
        *,
        user_id: int,
        run_id: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[EvaluationResult], int]:
        """分页获取测评结果，可按 run_id 过滤"""
        conditions = [
            EvaluationResult.user_id == user_id,
            EvaluationResult.deleted_at.is_(None),
        ]
        if run_id:
            conditions.append(EvaluationResult.run_id == run_id)

        total = await self.db.scalar(
            select(func.count())
            .select_from(EvaluationResult)
            .where(*conditions)
        )
        stmt = (
            select(EvaluationResult)
            .where(*conditions)
            .order_by(EvaluationResult.created_at.desc())
            .offset(page_size * (page - 1))
            .limit(page_size)
        )
        res = await self.db.scalars(stmt)
        return list(res.all()), total

    async def list_results_by_run(
        self, *, user_id: int, run_id: str
    ) -> list[EvaluationResult]:
        stmt = (
            select(EvaluationResult)
            .where(
                EvaluationResult.user_id == user_id,
                EvaluationResult.run_id == run_id,
                EvaluationResult.deleted_at.is_(None),
            )
            .order_by(EvaluationResult.created_at.asc())
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def get_result_by_id(self, *, user_id: int, result_id: str) -> EvaluationResult | None:
        stmt = (
            select(EvaluationResult)
            .where(
                EvaluationResult.user_id == user_id,
                EvaluationResult.id == result_id,
                EvaluationResult.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        return res.first()

    async def create_result(
        self,
        *,
        user_id: int,
        run_id: str,
        question_id: str,
        answer: str = "",
        status: EvaluationResultStatus = EvaluationResultStatus.PENDING,
        mrr: Decimal | None = None,
        correctness: Decimal | None = None,
        faithfulness: Decimal | None = None,
        retrieval_metrics: dict | None = None,
        latency_ms: int | None = None,
        trace_data: dict | None = None,
        error_message: str | None = None,
    ) -> EvaluationResult:
        result = EvaluationResult(
            user_id=user_id,
            run_id=run_id,
            question_id=question_id,
            answer=answer,
            status=status,
            mrr=mrr,
            correctness=correctness,
            faithfulness=faithfulness,
            retrieval_metrics=retrieval_metrics,
            latency_ms=latency_ms,
            trace_data=trace_data,
            error_message=error_message,
        )
        self.add(result)
        await self.commit()
        await self.refresh(result)
        return result

    async def batch_create_results(
        self, *, user_id: int, results: list[dict]
    ) -> list[EvaluationResult]:
        objs = []
        for r in results:
            obj = EvaluationResult(
                user_id=user_id,
                run_id=r["run_id"],
                question_id=r["question_id"],
                answer=r.get("answer", ""),
                status=r.get("status", EvaluationResultStatus.PENDING),
                mrr=r.get("mrr"),
                correctness=r.get("correctness"),
                faithfulness=r.get("faithfulness"),
                retrieval_metrics=r.get("retrieval_metrics"),
                latency_ms=r.get("latency_ms"),
                trace_data=r.get("trace_data"),
                error_message=r.get("error_message"),
            )
            objs.append(obj)
        self.db.add_all(objs)
        await self.db.flush()
        await self.commit()
        return objs

    async def claim_result(self, result_id: str) -> bool:
        """原子认领结果 — 仅当状态为 PENDING 时才改为 RUNNING。
        返回 True 表示认领成功，False 表示已被其他 worker 认领或已终态。
        """
        stmt = (
            update(EvaluationResult)
            .where(
                EvaluationResult.id == result_id,
                EvaluationResult.deleted_at.is_(None),
                EvaluationResult.status == EvaluationResultStatus.PENDING,
            )
            .values(
                status=EvaluationResultStatus.RUNNING,
                updated_at=datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(stmt)
        await self.commit()
        return result.rowcount == 1

    async def update_result(
        self,
        *,
        user_id: int,
        result_id: str,
        answer: str | None = None,
        status: EvaluationResultStatus | None = None,
        mrr: float | None = None,
        correctness: float | None = None,
        faithfulness: float | None = None,
        retrieval_metrics: dict | None = None,
        latency_ms: int | None = None,
        trace_data: dict | None = None,
        error_message: str | None = None,
    ) -> EvaluationResult | None:
        result = await self.get_result_by_id(user_id=user_id, result_id=result_id)
        if not result:
            return None
        if answer is not None:
            result.answer = answer
        if status is not None:
            result.status = status
        if mrr is not None:
            result.mrr = mrr
        if correctness is not None:
            result.correctness = correctness
        if faithfulness is not None:
            result.faithfulness = faithfulness
        if retrieval_metrics is not None:
            result.retrieval_metrics = retrieval_metrics
        if latency_ms is not None:
            result.latency_ms = latency_ms
        if trace_data is not None:
            result.trace_data = trace_data
        if error_message is not None:
            result.error_message = error_message
        await self.commit()
        await self.refresh(result)
        return result
    
    async def delete_result(self, *, user_id: int, result_id: str) -> bool:
        """软删除测评结果"""
        stmt = (
            update(EvaluationResult)
            .where(
                EvaluationResult.user_id == user_id,
                EvaluationResult.id == result_id,
                EvaluationResult.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self.db.execute(stmt)
        await self.commit()
        return result.rowcount > 0
    
    async def delete_results_by_run(self, *, user_id: int, run_id: str) -> int:
        """软删除指定 run_id 的所有测评结果"""
        stmt = (
            update(EvaluationResult)
            .where(
                EvaluationResult.user_id == user_id,
                EvaluationResult.run_id == run_id,
                EvaluationResult.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self.db.execute(stmt)
        await self.commit()
        return result.rowcount
