import asyncio
from decimal import Decimal
import json
import math
import time
from typing import Any, Tuple
import uuid
from langchain.chat_models import init_chat_model
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


from app.agents.prompts.evaluation_prompt import (
    build_check_eval_answer_correctness_prompt,
    build_check_eval_answer_faithfulness_prompt,
    build_eval_generate_question_prompt
)
from app.agents.workflows.qa_graph_workflow import ConfigContext, build_graph
from app.core.log_instance import worker_logger
from app.core.config import get_settings
from app.core.security import AESCipher
from app.db.repositories.evaluation_question_repository import EvaluationQuestionRepository
from app.db.repositories.evaluation_run_repository import EvaluationRunRepository
from app.db.repositories.evaluation_task_repository import (
    EvaluationResultRepository,
    EvaluationTaskRepository,
)
from app.db.repositories.model_config_repository import ModelConfigRepository
from app.integrations.embedding_provider import EmbeddingProvider, make_embedding_provider
from app.models.document_chunk import DocumentChunk
from app.models.evaluation import (
    EvaluationQuestion,
    EvaluationResultStatus,
    EvaluationTask,
    EvaluationTaskStatus,
    EvaluationTaskType,
)
from app.models.model_config import ModelConfig
from app.rag._query import QueryManager
from app.utils.format_number import format_number, format_number_ceil
from app.utils.time_ import time_cost


settings = get_settings()


async def handle_task(
    payload: dict[str, Any],
    session_maker: async_sessionmaker[AsyncSession],
    semaphore: asyncio.Semaphore | None = None
) -> None:
    """处理任务 — 通过 Run 原子认领保证多 worker 互斥"""
    task_id = payload.get("task_id")
    run_id = payload.get("run_id")
    user_id = payload.get("user_id")

    async with session_maker() as session:
        eval_task_repo = EvaluationTaskRepository(session)
        eval_run_repo = EvaluationRunRepository(session)

        # 1. 先查任务是否存在
        task: EvaluationTask | None = await eval_task_repo.get_task_by_id(user_id=user_id, task_id=task_id)
        if task is None:
            worker_logger.error(f"task not exists, task_id: {task_id}")
            return

        # 2. 查运行是否存在
        if run_id:
            run = await eval_run_repo.get_run_by_id(user_id=user_id, run_id=run_id)
            if run is None:
                worker_logger.error(f"run not exists, run_id: {run_id}")
                return

            # 3. 已终态 → 直接 ack
            if run.status in (EvaluationTaskStatus.COMPLETED, EvaluationTaskStatus.FAILED):
                worker_logger.info(f"run already finished, run_id: {run_id}, status: {run.status}")
                return

            # 4. 原子认领（PENDING 或 RUNNING超时 → RUNNING）
            claimed = await eval_run_repo.attempt_claim(run_id)
            if not claimed:
                worker_logger.info(
                    f"failed to claim run, run_id: {run_id}, status: {run.status}"
                )
                return False

            worker_logger.info(f"run claimed, run_id: {run_id}, type: {run.type}, status: {run.status}")

    # 5. 分发到具体处理器
    if task.type == EvaluationTaskType.GENERATE_QUESTION:
        await handle_evaluation_question_task(task_id, run_id, task.user_id, session_maker)
    elif task.type == EvaluationTaskType.RUN_EVALUATION:
        await handle_evaluation_task(task_id, run_id, task.user_id, session_maker, semaphore)
    else:
        worker_logger.error(f"unknown task type, task_id: {task_id}")
        return


@time_cost(_logger=worker_logger)
async def handle_evaluation_question_task(
    task_id: str, run_id: str, user_id: str, session_maker: async_sessionmaker[AsyncSession]
):
    """
    处理生成测评题目
    """
    try:
        worker_logger.info(f"task_id:{task_id} run_id:{run_id} generate evaluation question start")

        async with session_maker() as session:
            eval_task_repo = EvaluationTaskRepository(session)
            eval_task: EvaluationTask = await eval_task_repo.get_task_by_id(user_id=user_id, task_id=task_id)
            eval_run_repo = EvaluationRunRepository(session)
            eval_run = await eval_run_repo.get_run_by_id(user_id=user_id, run_id=run_id)

            config = eval_run.config or {}
            model_config_id = config.get("model_config_id")
            document_id = config.get("document_id")
            if not model_config_id or not document_id:
                raise ValueError(
                    f"task config missing required fields, "
                    f"model_config_id={model_config_id}, document_id={document_id}"
                )

            model_config_repo = ModelConfigRepository(session)
            model_config = await model_config_repo.get_by_id(
                user_id=user_id, model_config_id=model_config_id
            )
            if model_config is None:
                raise ValueError(f"model_config not found: {model_config_id}")

            document_chunks: list[DocumentChunk] = (
                await session.execute(
                    select(DocumentChunk).where(
                        DocumentChunk.knowledge_base_id == eval_run.knowledge_base_id,
                        DocumentChunk.document_id == document_id,
                        DocumentChunk.deleted_at.is_(None),
                    )
                )
            ).scalars().all()

            if not document_chunks:
                raise ValueError(f"no chunks found for document_id={document_id}")

            # 提取数据，关闭 session 前完成
            group_id = eval_task.group_id
            total_questions = eval_run.total_questions
            chat_model = model_config.chat_model
            provider = model_config.provider
            base_url = model_config.base_url
            encrypted_key = model_config.api_key_encrypted
            chunk_text = _format_chunk_content(document_chunks)

        # 构建 llm prompt
        api_key = (
            AESCipher(settings.aes_key_hex).decrypt(encrypted_key)
            if encrypted_key else ""
        )
        llm = _init_model(
            model=chat_model,
            model_provider=provider,
            api_key=api_key,
            base_url=base_url,
        )
        prompt = build_eval_generate_question_prompt()
        msg = prompt.format_messages(count=total_questions, text=chunk_text)

        worker_logger.info(f"task_id:{task_id} calling LLM...")
        response = await llm.ainvoke(msg)

        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            worker_logger.error(
                f"task_id:{task_id} LLM returned invalid JSON: {response.content[:500]}"
            )
            raise

        if not isinstance(result, list):
            raise ValueError(f"LLM result is not a list: {type(result)}")

        # 保存结果
        worker_logger.info(f"task_id:{task_id} saving {len(result)} questions...")
        async with session_maker() as session:
            question_repo = EvaluationQuestionRepository(session)
            question_objs = await question_repo.batch_create_questions(
                user_id=user_id,
                questions=[
                    {
                        "group_id": group_id,
                        "question": item["question"],
                        "expected_answer": item.get("answer", ""),
                        "source": "ai",
                    }
                    for item in result
                ]
            )

            chunk_objs = []
            for item, q in zip(result, question_objs):
                for chunk_id in item.get("chunk_id", []):
                    chunk_objs.append({"question_id": q.id, "chunk_id": chunk_id})

            if chunk_objs:
                await question_repo.batch_create_question_chunks(chunk_objs)

            # 更新运行状态为完成
            await EvaluationRunRepository(session).update_run(
                user_id=user_id,
                run_id=run_id,
                status=EvaluationTaskStatus.COMPLETED,
                completed_questions=len(question_objs),
            )

        worker_logger.info(f"task_id:{task_id} run_id:{run_id} completed, {len(question_objs)} questions")

    except Exception as e:
        worker_logger.exception(
            f"generate evaluation question task failed, task_id: {task_id}"
        )
        async with session_maker() as session:
            await EvaluationRunRepository(session).update_run(
                user_id=user_id,
                run_id=run_id,
                status=EvaluationTaskStatus.FAILED,
                error_message=f"{type(e).__name__}: {e}",
            )


@time_cost(_logger=worker_logger)
async def handle_evaluation_task(
    task_id: str,
    run_id: str,
    user_id: str,
    session_maker: async_sessionmaker[AsyncSession],
    semaphore: asyncio.Semaphore | None
):
    """
    处理执行评价
    """
    worker_logger.info(f"task_id:{task_id} run_id:{run_id} execute evaluation question start")

    # 心跳：每 60 秒续期 updated_at
    # 防止长时间运行被其他 worker 误判为超时重认领
    _heartbeat_stop = asyncio.Event()
    _heartbeat_task: asyncio.Task | None = None

    async def _heartbeat_loop():
        while not _heartbeat_stop.is_set():
            try:
                await asyncio.sleep(60)
                async with session_maker() as s:
                    repo = EvaluationRunRepository(s)
                    ok = await repo.heartbeat(run_id)
                    if not ok:
                        worker_logger.warning(
                            f"heartbeat failed for run_id={run_id}, "
                            f"run may have been stolen or already finished"
                        )
                        break  # run 已不再属于本 worker，停止心跳
            except asyncio.CancelledError:
                break
            except Exception as e:
                worker_logger.error(f"heartbeat error: {e}")

    _heartbeat_task = asyncio.create_task(_heartbeat_loop())

    try:
        async with session_maker() as session:
            eval_task_repo: EvaluationTaskRepository = EvaluationTaskRepository(session)
            eval_task = await eval_task_repo.get_task_by_id(user_id=user_id, task_id=task_id)
            # 查询问题
            question_repo: EvaluationQuestionRepository = EvaluationQuestionRepository(session)
            questions = await question_repo.get_question_by_ids(user_id=user_id, question_ids=eval_task.question_ids)
            # 查询模型配置
            eval_task_config = eval_task.config or {}
            model_config_id = eval_task_config.get("model_config_id")
            if not model_config_id:
                raise ValueError(f"task config missing model_config_id, task_id: {task_id}")

            model_config_repo: ModelConfigRepository = ModelConfigRepository(session)
            model_config: ModelConfig | None = await model_config_repo.get_by_id(
                user_id=user_id, model_config_id=model_config_id
            )
            if model_config is None:
                raise ValueError(f"model_config not found: {model_config_id}")
            # 为每个问题创建空结果（关联到 run）
            eval_result_repo: EvaluationResultRepository = EvaluationResultRepository(session)
            insert_result_list = []
            for qid in eval_task.question_ids:
                insert_result_list.append({
                    "run_id": run_id,
                    "question_id": qid,
                    "status": EvaluationResultStatus.PENDING,
                    "answer": "",
                })
            res_result = await eval_result_repo.batch_create_results(user_id=user_id, results=insert_result_list)

            knowledge_base_id = eval_task.knowledge_base_id
            chat_model = model_config.chat_model
            provider = model_config.provider
            base_url = model_config.base_url
            encrypted_key = model_config.api_key_encrypted
            questions_list = _format_question(questions)
            eval_result_id_list = [q.id for q in res_result]

        # 对话模型
        api_key = (
            AESCipher(settings.aes_key_hex).decrypt(encrypted_key)
            if encrypted_key else ""
        )
        llm = _init_model(
            model=chat_model,
            model_provider=provider,
            api_key=api_key,
            base_url=base_url,
        )

        # 向量模型
        embed_llm = await make_embedding_provider(
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
            model=settings.embedding_vector_model,
        )

        # 执行graph(批量执行)
        async def _run(
            _question: str,
            _thread_id: str,
            _question_id: str,
            _result_id: str
        ):
            try:
                if semaphore is not None:
                    async with semaphore:
                        await _run_graph(
                            session_maker=session_maker,
                            knowledge_base_id=knowledge_base_id,
                            user_id=user_id,
                            chat_llm=llm,
                            embed_llm=embed_llm,
                            thread_id=_thread_id,
                            question=_question,
                            run_id=run_id,
                            question_id=_question_id,
                            result_id=_result_id
                        )
                else:
                    await _run_graph(
                        session_maker=session_maker,
                        knowledge_base_id=knowledge_base_id,
                        user_id=user_id,
                        chat_llm=llm,
                        embed_llm=embed_llm,
                        thread_id=_thread_id,
                        question=_question,
                        run_id=run_id,
                        question_id=_question_id,
                        result_id=_result_id
                    )
            except Exception as e:
                worker_logger.error(f"执行graph失败: {e}")
                async with session_maker() as session:
                    eval_result_repo: EvaluationResultRepository = EvaluationResultRepository(session)
                    await eval_result_repo.update_result(
                        user_id=user_id,
                        result_id=_result_id,
                        status=EvaluationResultStatus.FAILED,
                        error_message=f"{type(e).__name__}: {e}",
                    )
                raise e

        # 并发执行
        features = {str(uuid.uuid4()): _question for _question in questions_list}

        results = await asyncio.gather(*[
            _run(_question["question"], _thread_id, _question["id"], _result_id)
            for (_thread_id, _question), _result_id in zip(features.items(), eval_result_id_list)
        ], return_exceptions=True)

        # 统计成功数，决定最终状态
        failed_count = sum(1 for r in results if isinstance(r, Exception))
        succeeded_count = len(questions_list) - failed_count


        # 更新运行状态
        async with session_maker() as session:
            eval_run_repo: EvaluationRunRepository = EvaluationRunRepository(session)
            eval_result_repo_new: EvaluationResultRepository = EvaluationResultRepository(session)

            # 统计平均指标
            questions = await eval_result_repo_new.list_results_by_run(user_id=user_id, run_id=run_id)
            questions_success = [q for q in questions if q.status == EvaluationResultStatus.SUCCESS]
            mrr = [q.mrr for q in questions if q.mrr]
            correctness = [q.correctness for q in questions_success if q.correctness]
            faithfulness = [q.faithfulness for q in questions_success if q.faithfulness]
            vector = [q.retrieval_metrics['vector_recall'] for q in questions_success if q.retrieval_metrics and q.retrieval_metrics.get('vector_recall')]
            bm25 = [q.retrieval_metrics['bm25_recall'] for q in questions_success if q.retrieval_metrics and q.retrieval_metrics.get('bm25_recall')]
            rrf = [q.retrieval_metrics['rrf_recall'] for q in questions_success if q.retrieval_metrics and q.retrieval_metrics.get('rrf_recall')]
            ranker = [q.retrieval_metrics['ranker_recall'] for q in questions_success if q.retrieval_metrics and q.retrieval_metrics.get('ranker_recall')]
            avg_mrr_score = format_number(sum(mrr) / len(mrr) if mrr else 0)
            avg_correctness_score = format_number(sum(correctness) / len(correctness) if correctness else 0)
            avg_faithfulness_score = format_number(sum(faithfulness) / len(faithfulness) if faithfulness else 0)
            avg_vector_recall = format_number_ceil(sum(vector) / len(vector) if vector else 0)
            avg_bm25_recall = format_number_ceil(sum(bm25) / len(bm25) if bm25 else 0)
            avg_rrf_recall = format_number_ceil(sum(rrf) / len(rrf) if rrf else 0)
            avg_ranker_recall = format_number_ceil(sum(ranker) / len(ranker) if ranker else 0)

            error_message = (
                None if failed_count == 0
                else f"{failed_count}/{len(questions_list)} questions failed" if succeeded_count > 0
                else f"all {len(questions_list)} questions failed"
            )

            await eval_run_repo.update_run(
                user_id=user_id,
                run_id=run_id,
                status=EvaluationTaskStatus.COMPLETED if succeeded_count > 0 else EvaluationTaskStatus.FAILED,
                completed_questions=succeeded_count,
                avg_recall={"vector_recall": avg_vector_recall, "bm25_recall": avg_bm25_recall, "rrf_recall": avg_rrf_recall, "ranker_recall": avg_ranker_recall},
                avg_mrr=avg_mrr_score,
                avg_correctness=avg_correctness_score,
                avg_faithfulness=avg_faithfulness_score,
                error_message=error_message,
            )

    except Exception as e:
        worker_logger.exception(f"task_id:{task_id} run_id:{run_id} execute evaluation question failed")
        async with session_maker() as session:
            eval_run_repo: EvaluationRunRepository = EvaluationRunRepository(session)
            await eval_run_repo.update_run(
                user_id=user_id,
                run_id=run_id,
                status=EvaluationTaskStatus.FAILED,
                error_message=f"{type(e).__name__}: {e}",
            )

    finally:
        _heartbeat_stop.set()
        if _heartbeat_task is not None:
            _heartbeat_task.cancel()
            try:
                await _heartbeat_task
            except asyncio.CancelledError:
                pass


def _init_model(
    model: str,
    model_provider: str,
    api_key: str,
    base_url: str,
    streaming: bool = False
):
    """初始化模型"""
    return init_chat_model(
        model=model,
        model_provider=model_provider,
        api_key=api_key,
        base_url=base_url,
        streaming=streaming,
    )


def _format_chunk_content(document_chunks: list[DocumentChunk]) -> str:
    """格式化文档块内容"""
    sorted_chunks = list(sorted(document_chunks, key=lambda chunk: chunk.chunk_index))
    return "\n".join([
        f"'chunk_id':{chunk.id}, 'chunk_content':{chunk.content}"
        for chunk in sorted_chunks
    ])


def _format_question(questions: list[EvaluationQuestion]):
    return [
        {
            "id": q.id,
            "question": q.question,
            "expected_answer": q.expected_answer,
            "source": q.source
        }
        for q in questions
    ]


@time_cost(_logger=worker_logger)
async def _run_graph(
    session_maker: async_sessionmaker[AsyncSession],
    knowledge_base_id: str,
    user_id: str,
    chat_llm: BaseChatModel,
    embed_llm: EmbeddingProvider,
    thread_id: str,
    question: str,
    run_id: str,
    question_id: str,
    result_id: str
):
    """
    执行graph

    :param session_maker: session_maker
    :param knowledge_base_id: 知识库id
    :param user_id: 用户id
    :param chat_llm: 对话模型
    :param embed_llm: 向量模型
    :param thread_id: 线程id
    :param question: 问题
    :param run_id: 运行ID
    :param question_id: 问题ID
    :param result_id: 结果ID
    """
    try:
        worker_logger.info(f"result_id: {result_id} start graph execute")
        # 原子认领结果 — 只有 PENDING 才能改为 RUNNING，防止多 worker 重复执行
        async with session_maker() as session:
            eval_result_repo: EvaluationResultRepository = EvaluationResultRepository(session)
            claimed = await eval_result_repo.claim_result(result_id=result_id)
            if not claimed:
                worker_logger.warning(
                    f"result_id: {result_id} already claimed or terminal, skipping"
                )
                return

        start_time = time.perf_counter()
        query_manager = QueryManager(chat_llm)
        history_messages = []
        # 构建graph
        rag_graph = build_graph()
        result = await rag_graph.ainvoke(
            {
                "query": question, "route": None, "force_rag": True,
                "queries": [], "keywords": [],
                "vector_retrieval_docs": [], "bm25_retrieval_docs": [],
                "rrf_docs": [], "sources": [], "ranked_docs": [], "ranked_sources": [],
                "answer": None, "trace": [], "is_error": False, "error_msg": ""
            },
            config={
                "configurable": {
                    "ctx": ConfigContext(
                        session_factory=session_maker,
                        knowledge_base_id=knowledge_base_id,
                        user_id=user_id,
                        llm=chat_llm,
                        embed_llm=embed_llm,
                        query_manager=query_manager,
                        history_messages=history_messages
                    ),
                    "thread_id": thread_id
                }
            },
        )

        # 处理结果
        await _handle_result(result, question, run_id, question_id, result_id, session_maker, chat_llm, user_id)

        end_time = time.perf_counter()
        latency_ms = math.ceil((end_time - start_time) * 100) / 100
        worker_logger.info(f"执行 测评 耗时: {latency_ms} s")
        # 更新结果耗时
        async with session_maker() as session:
            eval_result_repo: EvaluationResultRepository = EvaluationResultRepository(session)
            await eval_result_repo.update_result(
                user_id=user_id,
                result_id=result_id,
                latency_ms=latency_ms
            )

    except Exception as e:
        worker_logger.error(f"执行graph失败: {e}")
        async with session_maker() as session:
            eval_result_repo: EvaluationResultRepository = EvaluationResultRepository(session)
            await eval_result_repo.update_result(
                user_id=user_id,
                result_id=result_id,
                status=EvaluationResultStatus.FAILED,
                error_message=f"{type(e).__name__}: {e}",
            )

        raise e


@time_cost(_logger=worker_logger)
async def _handle_result(
    result: dict, question: str, run_id: str, question_id: str,
    result_id: str, session_maker: async_sessionmaker[AsyncSession],
    chat_llm: BaseChatModel, user_id: str
):
    """处理结果 — 将图执行结果写入 EvaluationResult"""
    try:
        worker_logger.info(f"result_id: {result_id} start handle result")

        # 幂等保护：如果已被另一个 worker 处理完毕，跳过重复计算
        async with session_maker() as session:
            existing = await EvaluationResultRepository(session).get_result_by_id(user_id=user_id, result_id=result_id)
            if existing and existing.status in (
                EvaluationResultStatus.SUCCESS, EvaluationResultStatus.FAILED
            ):
                worker_logger.warning(
                    f"result_id: {result_id} already terminal ({existing.status}), "
                    f"likely processed by another worker, skipping"
                )
                return

        answer = result.get("answer", "")
        vector_retrieval_docs = result.get("vector_retrieval_docs", [])
        bm25_retrieval_docs = result.get("bm25_retrieval_docs", [])
        rrf_docs = result.get("rrf_docs", [])
        ranked_docs = result.get("ranked_docs", [])
        ranked_sources = result.get("ranked_sources", [])
        trace = result.get("trace", [])
        is_error = result.get("is_error", False)
        error_msg = result.get("error_msg", "")

        async with session_maker() as session:
            eval_chunk_repo: EvaluationQuestionRepository = EvaluationQuestionRepository(session)
            questions_chunks = await eval_chunk_repo.get_chunks_by_question_id(
                question_id=question_id
            )
            question_item = await eval_chunk_repo.get_question_by_id(user_id=user_id, question_id=question_id)

            questions_chunk_ids = [chunk.chunk_id for chunk in questions_chunks]
            expected_answer = question_item.expected_answer if question_item else ""

        # 计算指标
        # mrr(倒排排名, 重排后的)
        mrr_score = 0
        for idx, item in enumerate(ranked_sources):
            chunk_id = item["document_chunk_id"]
            if chunk_id in questions_chunk_ids:
                mrr_score = 1 / (idx + 1)
                break

        # correctness(正确率), faithfulness(可信度), 用llm计算
        correctness = await _check_eval_answer_correctness(
            question=question,
            answer=expected_answer,
            model_answer=answer,
            chat_llm=chat_llm,
        )
        faithfulness = await _check_eval_answer_faithfulness(
            question=question,
            model_answer=answer,
            ranked_doc=ranked_docs,
            chat_llm=chat_llm,
        )

        # 计算retrieval_metrics(vector_recall, bm25_recall, rrf_recall, ranker_recall)
        retrieval_metrics = {
            "vector_recall": 0,
            "bm25_recall": 0,
            "rrf_recall": 0,
            "ranker_recall": 0
        }
        total_chunk_ids = len(questions_chunk_ids)
        worker_logger.info(f"total_chunk_ids length: {total_chunk_ids}")
        if total_chunk_ids == 0:
            worker_logger.warning(f"questions_chunk_ids is empty, question_id: {question_id}")

        else:
            # vector_recall
            vector_matched_ids = set()
            for vector_doc in vector_retrieval_docs:
                chunk_id = vector_doc.metadata["document_chunk_id"]
                if chunk_id in questions_chunk_ids:
                    vector_matched_ids.add(chunk_id)
            retrieval_metrics["vector_recall"] = len(vector_matched_ids) / total_chunk_ids
            # bm25_recall
            bm25_matched_ids = set()
            for bm25_doc in bm25_retrieval_docs:
                chunk_id = bm25_doc.metadata["document_chunk_id"]
                if chunk_id in questions_chunk_ids:
                    bm25_matched_ids.add(chunk_id)
            retrieval_metrics["bm25_recall"] = len(bm25_matched_ids) / total_chunk_ids
            # rrf_recall
            rrf_matched_ids = set()
            for rrf_doc in rrf_docs:
                chunk_id = rrf_doc.metadata["document_chunk_id"]
                if chunk_id in questions_chunk_ids:
                    rrf_matched_ids.add(chunk_id)
            retrieval_metrics["rrf_recall"] = len(rrf_matched_ids) / total_chunk_ids
            # ranker_recall
            ranker_matched_ids = set()
            for ranker_doc in ranked_docs:
                if isinstance(ranker_doc, tuple):
                    ranker_doc = ranker_doc[0]
                chunk_id = ranker_doc.metadata["document_chunk_id"]
                if chunk_id in questions_chunk_ids:
                    ranker_matched_ids.add(chunk_id)
            retrieval_metrics["ranker_recall"] = len(ranker_matched_ids) / total_chunk_ids

        # 更新结果
        async with session_maker() as session:
            eval_result_repo: EvaluationResultRepository = EvaluationResultRepository(session)
            await eval_result_repo.update_result(
                user_id=user_id,
                result_id=result_id,
                answer=answer,
                status=EvaluationResultStatus.FAILED if is_error else EvaluationResultStatus.SUCCESS,
                mrr=format_number(mrr_score),
                correctness=format_number(correctness.get("score", 0)),
                faithfulness=format_number(faithfulness.get("score", 0)),
                retrieval_metrics=retrieval_metrics,
                trace_data={"trace": trace, "correctness": correctness, "faithfulness": faithfulness},
                error_message=error_msg if is_error else None,
            )

    except Exception as e:
        worker_logger.error(f"处理结果失败: {e}")
        async with session_maker() as session:
            eval_result_repo: EvaluationResultRepository = EvaluationResultRepository(session)
            await eval_result_repo.update_result(
                user_id=user_id,
                result_id=result_id,
                status=EvaluationResultStatus.FAILED,
                error_message=f"{type(e).__name__}: {e}",
            )

        raise e


@time_cost(_logger=worker_logger)
async def _check_eval_answer_correctness(
    question: str, answer: str, model_answer: str, chat_llm: BaseChatModel
) -> dict:
    """检查答案的正确性"""
    prompt: ChatPromptTemplate = build_check_eval_answer_correctness_prompt()
    msg = prompt.format_messages(
        question=question,
        answer=answer,
        model_answer=model_answer,
    )
    response = await chat_llm.ainvoke(msg)

    if isinstance(response, tuple):
        response = response[0]
    result = json.loads(response.content)

    return result

@time_cost(_logger=worker_logger)
async def _check_eval_answer_faithfulness(
    question: str, model_answer: str, ranked_doc: list[Document], chat_llm: BaseChatModel
) -> dict:
    """检查答案的可信度"""
    # 上下文查询
    context = await _get_context(ranked_doc)
    prompt: ChatPromptTemplate = build_check_eval_answer_faithfulness_prompt()
    msg = prompt.format_messages(
        question=question,
        model_answer=model_answer,
        context=context
    )
    response = await chat_llm.ainvoke(msg)

    if isinstance(response, tuple):
        response = response[0]
    result = json.loads(response.content)

    return result


async def _get_context(ranked_doc: list[Document]) -> str:
    """获取上下文"""
    context = []
    for doc in ranked_doc:
        # 兼容 (Document, score) 元组格式
        if isinstance(doc, tuple):
            doc = doc[0]
        if doc.page_content:
            context.append(doc.page_content)

    return "\n".join(context)
