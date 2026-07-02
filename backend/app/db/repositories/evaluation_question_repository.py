from datetime import datetime, timezone

from sqlalchemy import func, select, update, delete

from app.db.repositories._base import BaseRepository
from app.models.evaluation import EvaluationQuestion, EvaluationQuestionChunk


class EvaluationQuestionRepository(BaseRepository):

    async def get_question_all(self, *, user_id: int) -> list[EvaluationQuestion]:
        stmt = select(EvaluationQuestion).where(
            EvaluationQuestion.user_id == user_id,
            EvaluationQuestion.deleted_at.is_(None),
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def get_question_by_id(self, *, user_id: int, question_id: str) -> EvaluationQuestion | None:
        stmt = (
            select(EvaluationQuestion)
            .where(
                EvaluationQuestion.user_id == user_id,
                EvaluationQuestion.id == question_id,
                EvaluationQuestion.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        return res.first()

    async def get_question_by_ids(self, *, user_id: int, question_ids: list[str]) -> list[EvaluationQuestion]:
        stmt = (
            select(EvaluationQuestion)
            .where(
                EvaluationQuestion.user_id == user_id,
                EvaluationQuestion.id.in_(question_ids),
                EvaluationQuestion.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def list_questions(
        self, *, user_id: int, page: int = 1, page_size: int = 10, group_id: str | None = None
    ) -> tuple[list[EvaluationQuestion], int]:
        """分页获取测评问题列表"""
        conditions = [
            EvaluationQuestion.user_id == user_id,
            EvaluationQuestion.deleted_at.is_(None),
        ]
        if group_id:
            conditions.append(EvaluationQuestion.group_id == group_id)

        total = await self.db.scalar(
            select(func.count())
            .select_from(EvaluationQuestion)
            .where(*conditions)
        )
        stmt = (
            select(EvaluationQuestion)
            .where(*conditions)
            .order_by(EvaluationQuestion.created_at)
            .offset(page_size * (page - 1))
            .limit(page_size)
        )
        res = await self.db.scalars(stmt)
        return list(res.all()), total

    async def get_questions_by_group_id(self, *, user_id: int, group_id: str) -> list[EvaluationQuestion]:
        """获取某个分组下所有未删除的问题"""
        stmt = (
            select(EvaluationQuestion)
            .where(
                EvaluationQuestion.user_id == user_id,
                EvaluationQuestion.group_id == group_id,
                EvaluationQuestion.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def create_question(
        self, *, user_id: int, group_id: str, question: str, expected_answer: str | None = None, source: str = "user"
    ) -> EvaluationQuestion:
        eq = EvaluationQuestion(
            user_id=user_id,
            group_id=group_id,
            question=question,
            expected_answer=expected_answer,
            source=source,
        )
        self.add(eq)
        await self.commit()
        await self.refresh(eq)
        return eq

    async def batch_create_questions(
        self, *, user_id: int, questions: list[dict]
    ) -> list[EvaluationQuestion]:
        """批量创建问题"""
        objs = []
        for q in questions:
            obj = EvaluationQuestion(
                user_id=user_id,
                group_id=q.get("group_id", ""),
                question=q["question"],
                expected_answer=q.get("expected_answer"),
                source=q.get("source", "ai"),
            )
            objs.append(obj)
        self.db.add_all(objs)
        await self.db.flush()
        await self.commit()
        return objs

    async def update_question(
        self,
        *,
        user_id: int,
        question_id: str,
        group_id: str | None = None,
        question: str | None = None,
        expected_answer: str | None = None,
        source: str | None = None,
    ) -> EvaluationQuestion | None:
        eq = await self.get_question_by_id(user_id=user_id, question_id=question_id)
        if not eq:
            return None
        if group_id is not None:
            eq.group_id = group_id
        if question is not None:
            eq.question = question
        if expected_answer is not None:
            eq.expected_answer = expected_answer
        if source is not None:
            eq.source = source
        await self.commit()
        await self.refresh(eq)
        return eq

    async def delete_question(self, *, user_id: int, question_id: str) -> bool:
        """软删除测评问题"""
        stmt = (
            update(EvaluationQuestion)
            .where(
                EvaluationQuestion.user_id == user_id,
                EvaluationQuestion.id == question_id,
                EvaluationQuestion.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self.db.execute(stmt)
        await self.commit()
        return result.rowcount > 0

    async def get_chunks_by_question_id(
        self, question_id: str
    ) -> list[EvaluationQuestionChunk]:
        stmt = (
            select(EvaluationQuestionChunk)
            .where(EvaluationQuestionChunk.question_id == question_id)
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def create_question_chunk(
        self, question_id: str, chunk_id: str
    ) -> EvaluationQuestionChunk:
        qc = EvaluationQuestionChunk(
            question_id=question_id,
            chunk_id=chunk_id,
        )
        self.add(qc)
        await self.commit()
        await self.refresh(qc)
        return qc

    async def batch_create_question_chunks(
        self, question_chunks: list[dict]
    ) -> list[EvaluationQuestionChunk]:
        objs = []
        for qc in question_chunks:
            obj = EvaluationQuestionChunk(
                question_id=qc["question_id"],
                chunk_id=qc["chunk_id"],
            )
            objs.append(obj)
        self.db.add_all(objs)
        await self.db.flush()
        await self.commit()
        return objs

    async def delete_chunks_by_question_id(self, question_id: str) -> None:
        """删除问题关联的所有chunk"""
        stmt = delete(EvaluationQuestionChunk).where(
            EvaluationQuestionChunk.question_id == question_id
        )
        await self.db.execute(stmt)
        await self.commit()
