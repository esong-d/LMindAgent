from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.db.redis_db.queue import RedisStreamQueue
from app.db.repositories.chunk_repository import ChunkRepository
from app.db.repositories.evaluation_group_repository import EvaluationGroupRepository
from app.db.repositories.evaluation_question_repository import EvaluationQuestionRepository
from app.db.repositories.evaluation_run_repository import EvaluationRunRepository
from app.db.repositories.evaluation_task_repository import (
    EvaluationTaskRepository,
    EvaluationResultRepository,
)
from app.db.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.db.repositories.model_config_repository import ModelConfigRepository
from app.models.evaluation import EvaluationTaskStatus, EvaluationTaskType


class EvaluationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.groups = EvaluationGroupRepository(db)
        self.questions = EvaluationQuestionRepository(db)
        self.tasks = EvaluationTaskRepository(db)
        self.runs = EvaluationRunRepository(db)
        self.results = EvaluationResultRepository(db)
        self.document_chunk = ChunkRepository(db)
        self.knowledge_base = KnowledgeBaseRepository(db)
        self.model_config = ModelConfigRepository(db)
        self.queue = RedisStreamQueue(stream="evaluation", group="evaluation_worker")

    async def get_all_groups(self, user_id: int) -> list[dict]:
        groups = await self.groups.get_all_groups(user_id=user_id)
        return [{"id": g.id, "name": g.name} for g in groups]

    async def group_list(
        self, user_id: int, page: int = 1, page_size: int = 10
    ) -> dict:
        items, total = await self.groups.list_groups(user_id=user_id, page=page, page_size=page_size)
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def create_group(
        self, user_id: int, name: str, description: str = ""
    ) -> dict:
        group = await self.groups.create_group(user_id=user_id, name=name, description=description)
        return group

    async def update_group(
        self, user_id: int, group_id: str, *,
        name: str | None = None, description: str | None = None,
    ) -> dict:
        group = await self.groups.update_group(
            user_id=user_id, group_id=group_id, name=name, description=description,
        )
        if not group:
            raise NotFoundError("测评组不存在")
        return group

    async def delete_group(self, user_id: int, group_id: str) -> bool:
        ok = await self.groups.delete_group(user_id=user_id, group_id=group_id)
        if not ok:
            raise NotFoundError("测评组不存在")
        return True

    async def evaluation_question_list(
        self, user_id: int, page: int = 1, page_size: int = 10, group_id: str | None = None
    ) -> dict:
        items, total = await self.questions.list_questions(
            user_id=user_id, page=page, page_size=page_size, group_id=group_id
        )
        # 分组信息
        group_ids = [t.group_id for t in items]
        groups = await self.groups.get_group_by_ids(user_id=user_id, group_ids=group_ids)
        groups_dict = {g.id: {"id": g.id, "name": g.name} for g in groups}

        item_list = [
            {
                **t.__dict__,
                "group": groups_dict.get(t.group_id, {}),
            }
            for t in items
        ]
        return {
            "items": item_list,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_questions_by_group_id(self, user_id: int, group_id: str) -> list[dict]:
        questions = await self.questions.get_questions_by_group_id(user_id=user_id, group_id=group_id)
        return [{"id": q.id, "question": q.question} for q in questions]

    async def question_detail(
        self, user_id: int, question_id: str
    ) -> dict:
        question = await self.questions.get_question_by_id(user_id=user_id, question_id=question_id)
        if not question:
            raise NotFoundError("测评问题不存在")

        chunks = await self.questions.get_chunks_by_question_id(question_id)
        chunk_ids = [c.chunk_id for c in chunks]
        chunk_sources = await self.document_chunk.get_by_ids(user_id=user_id, chunk_ids=chunk_ids)
        chunk_sources_list = [{"id": s.id, "content": s.content} for s in chunk_sources]

        # 分组信息
        group = await self.groups.get_group_by_id(user_id=user_id, group_id=question.group_id)
        result = {
            "id": question.id,
            "group": {"id": group.id, "name": group.name} if group else {},
            "question": question.question,
            "expected_answer": question.expected_answer,
            "source": question.source,
            "created_at": question.created_at,
            "chunks": chunk_sources_list,
        }
        return result

    async def create_question(
        self,
        user_id: int,
        source: str,
        group_id: str,
        question_count: int = 1,
        *,
        question: str | None = None,
        expected_answer: str | None = None,
        chunk_ids: list[str] | None = None,
        knowledge_base_id: str | None = None,
        document_id: str | None = None,
        model_config_id: str | None = None
    ) -> dict:
        if source == "human":
            raise NotImplementedError("人工生成问题功能尚未实现")

        elif source == "ai":
            # 创建任务模板
            task = await self.tasks.create_task(
                user_id=user_id,
                group_id=group_id,
                name="AI生成测评问题",
                type=EvaluationTaskType.GENERATE_QUESTION,
                knowledge_base_id=knowledge_base_id,
                total_questions=question_count,
                config={"document_id": document_id, "model_config_id": model_config_id},
            )
        else:
            raise ValueError("source 参数无效")

        return {"id": task.id, "status": "pending"}

    async def update_question(
        self,
        user_id: int,
        question_id: str,
        *,
        group_id: str | None = None,
        question: str | None = None,
        expected_answer: str | None = None,
        source: str | None = None,
    ) -> dict:
        eq = await self.questions.update_question(
            user_id=user_id,
            question_id=question_id,
            group_id=group_id,
            question=question,
            expected_answer=expected_answer,
            source=source,
        )
        if not eq:
            raise NotFoundError("测评问题不存在")
        chunks = await self.questions.get_chunks_by_question_id(question_id)
        return {
            "id": eq.id,
            "group_id": eq.group_id,
            "question": eq.question,
            "expected_answer": eq.expected_answer,
            "source": eq.source,
            "created_at": eq.created_at,
            "chunk_ids": [c.chunk_id for c in chunks],
        }

    async def delete_question(self, user_id: int, question_id: str) -> bool:
        ok = await self.questions.delete_question(user_id=user_id, question_id=question_id)
        if not ok:
            raise NotFoundError("测评问题不存在")
        # 同时删除关联的 chunks
        await self.questions.delete_chunks_by_question_id(question_id)
        return True

    async def task_list(
        self, user_id: int, page: int = 1, page_size: int = 10, group_id: str | None = None
    ) -> dict:
        items, total = await self.tasks.list_tasks(
            user_id=user_id, page=page, page_size=page_size, group_id=group_id
        )
        # 分组信息
        group_ids = [t.group_id for t in items]
        groups = await self.groups.get_group_by_ids(user_id=user_id, group_ids=group_ids)
        groups_dict = {g.id: {"id": g.id, "name": g.name} for g in groups}
        # 知识库
        knowledge_base_ids = [t.knowledge_base_id for t in items]
        knowledge_bases = await self.knowledge_base.get_by_knowledge_ids(
            user_id=user_id, knowledge_ids=knowledge_base_ids
        )
        knowledge_bases_dict = {kb.id: {"id": kb.id, "name": kb.name} for kb in knowledge_bases}

        item_list = [
            {
                **t.__dict__,
                "group": groups_dict.get(t.group_id, {}),
                "knowledge_base": knowledge_bases_dict.get(t.knowledge_base_id, {}),
            }
            for t in items
        ]

        return {
            "items": item_list,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def task_detail(self, user_id: int, task_id: str) -> dict:
        task = await self.tasks.get_task_by_id(user_id=user_id, task_id=task_id)
        if not task:
            raise NotFoundError("测评任务不存在")

        group = await self.groups.get_group_by_id(user_id=user_id, group_id=task.group_id)
        knowledge_base = await self.knowledge_base.get_by_id(
            user_id=user_id, knowledge_base_id=task.knowledge_base_id
        )

        return {
            **task.__dict__,
            "group": {"id": group.id, "name": group.name} if group else {},
            "knowledge_base": {"id": knowledge_base.id, "name": knowledge_base.name} if knowledge_base else {},
        }

    async def create_task(
        self,
        user_id: int,
        name: str,
        group_id: str,
        knowledge_base_id: str,
        model_config_id: str,
        question_ids: list[str] | None = None,
    ) -> dict:
        # 验证组存在
        group = await self.groups.get_group_by_id(user_id=user_id, group_id=group_id)
        if not group:
            raise NotFoundError("测评组不存在")

        # 未传 question_ids 则使用该组下所有问题
        if not question_ids:
            questions = await self.questions.get_questions_by_group_id(user_id=user_id, group_id=group_id)
            question_ids = [q.id for q in questions]
        else:
            # 验证所有问题存在
            questions = await self.questions.get_question_by_ids(user_id=user_id, question_ids=question_ids)
            if len(question_ids) != len(questions):
                raise NotFoundError(f"有测评问题不存在")

        task = await self.tasks.create_task(
            name=name,
            group_id=group_id,
            user_id=user_id,
            type=EvaluationTaskType.RUN_EVALUATION,
            knowledge_base_id=knowledge_base_id,
            total_questions=len(question_ids),
            config={"model_config_id": model_config_id},
            question_ids=question_ids,
        )

        return {
            "id": task.id,
            "name": task.name,
            "group_id": task.group_id,
            "knowledge_base_id": task.knowledge_base_id,
            "total_questions": task.total_questions,
            "question_ids": task.question_ids,
            "config": task.config,
            "created_at": task.created_at,
        }

    async def delete_task(self, user_id: int, task_id: str) -> bool:
        ok = await self.tasks.delete_task(user_id=user_id, task_id=task_id)
        if not ok:
            raise NotFoundError("测评任务不存在")

        return True

    async def run_list(
        self, user_id: int, page: int = 1, page_size: int = 10,
        task_id: str | None = None,
    ) -> dict:
        items, total = await self.runs.list_runs(
            user_id=user_id, page=page, page_size=page_size, task_id=task_id
        )
        # 知识库信息
        knowledge_base_ids = [r.knowledge_base_id for r in items]
        knowledge_bases = await self.knowledge_base.get_by_knowledge_ids(
            user_id=user_id, knowledge_ids=knowledge_base_ids
        )
        knowledge_bases_dict = {
            kb.id: {"id": kb.id, "name": kb.name} for kb in knowledge_bases
        }
        # 模型配置信息
        model_config = await self.model_config.all(user_id=user_id)
        model_config_dict = {mc.id: {"id": mc.id, "name": mc.name, "provider": mc.provider} for mc in model_config}

        return {
            "items": [{
                **item.__dict__,
                "model": model_config_dict.get(item.config["model_config_id"], {}),
                "knowledge_base": knowledge_bases_dict.get(item.knowledge_base_id, {}),
            } for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def run_detail(self, user_id: int, run_id: str) -> dict:
        run = await self.runs.get_run_by_id(user_id=user_id, run_id=run_id)
        if not run:
            raise NotFoundError("测评运行不存在")

        # 查询知识库
        knowledge_base = await self.knowledge_base.get_by_id(
            user_id=user_id, knowledge_base_id=run.knowledge_base_id
        )
        # 模型配置
        model_config = await self.model_config.get_by_id(
            user_id=user_id, model_config_id=run.config["model_config_id"]
        )

        return {
            **run.__dict__,
            "model": {"id": model_config.id, "name": model_config.name, "provider": model_config.provider} if model_config else {},
            "knowledge_base": {"id": knowledge_base.id, "name": knowledge_base.name} if knowledge_base else {},
        }

    async def delete_run(self, user_id: int, run_id: str) -> bool:
        ok = await self.runs.delete_run(user_id=user_id, run_id=run_id)
        if not ok:
            raise NotFoundError("测评运行不存在")
        # 同时删除关联的测评结果
        await self.results.delete_results_by_run(user_id=user_id, run_id=run_id)
        
        return True

    async def execute_evaluation(self, user_id: int, task_id: str) -> dict:
        task = await self.tasks.get_task_by_id(user_id=user_id, task_id=task_id)
        if not task:
            raise NotFoundError("测评任务不存在")

        # 创建运行实例
        run = await self.runs.create_run(
            user_id=user_id,
            task_id=task.id,
            type=task.type,
            knowledge_base_id=task.knowledge_base_id,
            total_questions=task.total_questions,
            question_ids=task.question_ids,
            config=task.config,
        )

        # 入队
        queue_res = await self.queue.add(data={"task_id": task.id, "run_id": run.id, "user_id": user_id})

        return {
            "task_id": task.id,
            "run_id": run.id,
            "queue_id": queue_res,
        }

    async def get_evaluation_result(
        self, user_id: int, run_id: str | None = None,
        page: int = 1, page_size: int = 10,
    ) -> dict:
        """测评结果列表，可按 run_id 过滤"""
        items, total = await self.results.list_results(
            user_id=user_id, run_id=run_id, page=page, page_size=page_size
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_result_detail(
        self, user_id: int, result_id: str
    ) -> dict:
        """单条测评结果详情"""
        result = await self.results.get_result_by_id(user_id=user_id, result_id=result_id)
        if not result:
            raise NotFoundError("测评结果不存在")

        # 关联查询问题信息
        question = await self.questions.get_question_by_id(user_id=user_id, question_id=result.question_id)
        run = await self.runs.get_run_by_id(user_id=user_id, run_id=result.run_id)
        task = await self.tasks.get_task_by_id(user_id=user_id, task_id=run.task_id) if run else None
        group = await self.groups.get_group_by_id(user_id=user_id, group_id=question.group_id) if question else None
        return {
            "result": result,
            "question": {**question.__dict__, "group": {"id": group.id, "name": group.name}} if question and group else None,
            "task_name": task.name if task else None,
        }
