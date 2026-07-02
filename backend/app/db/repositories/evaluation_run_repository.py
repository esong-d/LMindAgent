from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select, update

from app.db.repositories._base import BaseRepository
from app.models.evaluation import (
    EvaluationRun,
    EvaluationTaskStatus,
    EvaluationTaskType,
)


class EvaluationRunRepository(BaseRepository):
    """测评运行 Repository"""

    async def attempt_claim(
        self, run_id: str, *, stale_timeout_seconds: int = 1800
    ) -> bool:
        """原子认领运行
        只有 PENDING 或 RUNNING超时 才能抢到。
        返回 True 表示认领成功, False 表示已被其他 worker 认领。
        默认超时 30 分钟。
        """
        stale_threshold = datetime.now(timezone.utc) - timedelta(
            seconds=stale_timeout_seconds
        )
        result = await self.db.execute(
            update(EvaluationRun)
            .where(
                EvaluationRun.id == run_id,
                EvaluationRun.deleted_at.is_(None),
                (
                    (EvaluationRun.status == EvaluationTaskStatus.PENDING)
                    | (
                        (EvaluationRun.status == EvaluationTaskStatus.RUNNING)
                        & (EvaluationRun.updated_at < stale_threshold)
                    )
                ),
            )
            .values(
                status=EvaluationTaskStatus.RUNNING,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.commit()
        return result.rowcount == 1

    async def heartbeat(self, run_id: str) -> bool:
        """心跳续期 — 仅更新 updated_at，防止被其他 worker 误判为超时。
        返回 True 表示续期成功, False 表示 run 不存在或已终态。
        """
        result = await self.db.execute(
            update(EvaluationRun)
            .where(
                EvaluationRun.id == run_id,
                EvaluationRun.deleted_at.is_(None),
                EvaluationRun.status == EvaluationTaskStatus.RUNNING,
            )
            .values(updated_at=datetime.now(timezone.utc))
        )
        await self.commit()
        return result.rowcount == 1

    async def list_runs(
        self,
        *,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        task_id: str | None = None,
    ) -> tuple[list[EvaluationRun], int]:
        """分页获取运行列表，可按 task_id 过滤"""
        conditions = [
            EvaluationRun.user_id == user_id,
            EvaluationRun.deleted_at.is_(None),
        ]
        if task_id:
            conditions.append(EvaluationRun.task_id == task_id)

        total = await self.db.scalar(
            select(func.count())
            .select_from(EvaluationRun)
            .where(*conditions)
        )
        stmt = (
            select(EvaluationRun)
            .where(*conditions)
            .order_by(EvaluationRun.created_at.desc())
            .offset(page_size * (page - 1))
            .limit(page_size)
        )
        res = await self.db.scalars(stmt)
        return list(res.all()), total

    async def get_run_by_id(self, *, user_id: int, run_id: str) -> EvaluationRun | None:
        stmt = (
            select(EvaluationRun)
            .where(
                EvaluationRun.user_id == user_id,
                EvaluationRun.id == run_id,
                EvaluationRun.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        return res.first()

    async def create_run(
        self,
        *,
        user_id: int,
        task_id: str,
        type: EvaluationTaskType,
        knowledge_base_id: str,
        total_questions: int = 0,
        question_ids: list[str] | None = None,
        config: dict | None = None,
    ) -> EvaluationRun:
        run = EvaluationRun(
            user_id=user_id,
            task_id=task_id,
            type=type,
            status=EvaluationTaskStatus.PENDING,
            knowledge_base_id=knowledge_base_id,
            total_questions=total_questions,
            completed_questions=0,
            question_ids=question_ids or [],
            config=config or {},
        )
        self.add(run)
        await self.commit()
        await self.refresh(run)
        return run

    async def update_run(
        self,
        *,
        user_id: int,
        run_id: str,
        status: EvaluationTaskStatus | None = None,
        completed_questions: int | None = None,
        avg_recall: dict | None = None,
        avg_mrr: Decimal | None = None,
        avg_correctness: Decimal | None = None,
        avg_faithfulness: Decimal | None = None,
        error_message: str | None = None,
    ) -> EvaluationRun | None:
        run = await self.get_run_by_id(user_id=user_id, run_id=run_id)
        if not run:
            return None
        if status is not None:
            run.status = status
        if completed_questions is not None:
            run.completed_questions = completed_questions
        if avg_recall is not None:
            run.avg_recall = avg_recall
        if avg_mrr is not None:
            run.avg_mrr = avg_mrr
        if avg_correctness is not None:
            run.avg_correctness = avg_correctness
        if avg_faithfulness is not None:
            run.avg_faithfulness = avg_faithfulness
        if error_message is not None:
            run.error_message = error_message

        await self.commit()
        await self.refresh(run)
        return run

    async def delete_run(self, *, user_id: int, run_id: str) -> bool:
        """软删除测评运行"""
        stmt = (
            update(EvaluationRun)
            .where(
                EvaluationRun.user_id == user_id,
                EvaluationRun.id == run_id,
                EvaluationRun.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self.db.execute(stmt)
        await self.commit()
        return result.rowcount > 0
