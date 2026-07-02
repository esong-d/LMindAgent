
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, Float, Enum, JSON, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.models.base import BaseMUUID


class EvaluationGroup(BaseMUUID):
    __tablename__ = "evaluation_group"
    __table_args__ = (
        {"comment": "测评问题组"}
    )

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    name: Mapped[str] = mapped_column(String(200), comment="组名称")
    description: Mapped[str] = mapped_column(Text, comment="组描述")


class EvaluationQuestion(BaseMUUID):
    __tablename__ = "evaluation_question"
    __table_args__ = (
        {"comment": "测评问题"}
    )

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    group_id: Mapped[str] = mapped_column(ForeignKey("evaluation_group.id"), comment="组ID")
    question: Mapped[str] = mapped_column(Text, comment="The question text")
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True, comment="expected_answer")
    # 来源：ai, human, user
    source: Mapped[str] = mapped_column(String(20), default="ai")



class EvaluationQuestionChunk(BaseMUUID):
    __tablename__ = "evaluation_question_chunk"
    __table_args__ = (
        {"comment": "测评问题片段"}
    )

    question_id: Mapped[str] = mapped_column(ForeignKey("evaluation_question.id"))
    chunk_id: Mapped[str] = mapped_column(String(255), comment="The chunk id")


class EvaluationTaskStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationTaskType(enum.Enum):
    GENERATE_QUESTION = "generate_question"
    RUN_EVALUATION = "run_evaluation"


class EvaluationTask(BaseMUUID):
    __tablename__ = "evaluation_task"
    __table_args__ = (
        {"comment": "测评任务"}
    )

    name: Mapped[str] = mapped_column(String(200), comment="任务名称")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    group_id: Mapped[str] = mapped_column(ForeignKey("evaluation_group.id"), comment="组ID")
    question_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True, comment="问题ID列表")
    type: Mapped[EvaluationTaskType] = mapped_column(Enum(EvaluationTaskType), comment="任务类型")
    knowledge_base_id: Mapped[str] = mapped_column(String(32), comment="知识库ID")
    total_questions: Mapped[int] = mapped_column(Integer, default=0, comment="总问题数")
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="配置")



class EvaluationRun(BaseMUUID):
    __tablename__ = "evaluation_run"
    __table_args__ = (
        {"comment": "测评运行"}
    )
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    task_id: Mapped[str] = mapped_column(ForeignKey("evaluation_task.id"), comment="任务ID")
    question_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True, comment="问题ID列表")
    type: Mapped[EvaluationTaskType] = mapped_column(Enum(EvaluationTaskType), comment="任务类型")
    status: Mapped[EvaluationTaskStatus] = mapped_column(Enum(EvaluationTaskStatus), comment="任务状态")
    knowledge_base_id: Mapped[str] = mapped_column(String(32), comment="知识库ID")
    total_questions: Mapped[int] = mapped_column(Integer, default=0, comment="总问题数")
    completed_questions: Mapped[int] = mapped_column(Integer, default=0, comment="已完成问题数")
    avg_recall: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="平均召回率")
    avg_mrr: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=True, comment="平均MRR")
    avg_correctness: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=True, comment="平均正确性")
    avg_faithfulness: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=True, comment="平均忠实度")
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="配置")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class EvaluationResultStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class EvaluationResult(BaseMUUID):
    __tablename__ = "evaluation_result"
    __table_args__ = (
        {"comment": "测评结果"}
    )

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    run_id: Mapped[str] = mapped_column(ForeignKey("evaluation_run.id"), comment="运行ID")
    question_id: Mapped[str] = mapped_column(ForeignKey("evaluation_question.id"), comment="问题ID")
    answer: Mapped[str] = mapped_column(Text, comment="回答")
    status: Mapped[EvaluationResultStatus] = mapped_column(Enum(EvaluationResultStatus), comment="状态")
    # 核心指标（单独字段）
    mrr: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=True, comment="MRR")
    correctness: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=True, comment="正确性")
    faithfulness: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=True, comment="忠实度")
    # 检索指标（JSON）
    #  vector_recall, bm25_recall, rrf_recall, ranker_recall
    retrieval_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="检索指标")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="耗时")
    # vector_docs, bm25_docs, rrf_docs, ranker_docs
    trace_data: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="追踪数据")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
