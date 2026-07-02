from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.evaluation import EvaluationResultStatus, EvaluationTaskStatus, EvaluationTaskType


class KnowledgeBaseOut(BaseModel):
    """知识库出参"""
    id: str
    name: str

class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200, description="组名称")
    description: str = Field(default="", description="组描述")


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class GroupOut(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GroupAllItem(BaseModel):
    id: str
    name: str


class GroupListOut(BaseModel):
    items: list[GroupOut]
    total: int
    page: int
    page_size: int



class QuestionCreate(BaseModel):
    """创建测评问题 — source=human 需传 question/expected_answer/chunk_ids，
       source=ai 需传 knowledge_base_id/document_id"""
    source: str = Field(..., description="来源: ai / human")
    group_id: str = Field(..., description="所属组ID")

    # human 方式字段
    question: str | None = Field(default=None, min_length=1, description="问题文本 (human必填)")
    expected_answer: str | None = Field(default=None, description="预期答案 (human必填)")
    chunk_ids: list[str] | None = Field(default=None, description="关联chunk (human可选)")

    # ai 方式字段
    knowledge_base_id: str | None = Field(default=None, description="知识库ID (ai必填)")
    document_id: str | None = Field(default=None, description="文档ID (ai必填)")
    question_count: int | None = Field(default=None, description="问题数量 (ai必填)")
    model_config_id: str | None = Field(default=None, description="模型配置ID (ai必填)")

    @model_validator(mode="after")
    def validate_by_source(self):
        if self.source == "human":
            if not self.question:
                raise ValueError("source=human 时必须提供 question")

        elif self.source == "ai":
            if not self.knowledge_base_id:
                raise ValueError("source=ai 时必须提供 knowledge_base_id")
            if not self.document_id:
                raise ValueError("source=ai 时必须提供 document_id")
            if not self.question_count:
                raise ValueError("source=ai 时必须提供 question_count")
            if not self.model_config_id:
                raise ValueError("source=ai 时必须提供 model_config_id")

        else:
            raise ValueError(f"不支持的 source: {self.source}，可选值: ai / human")

        return self


class QuestionUpdate(BaseModel):
    """更新测评问题"""
    group_id: str | None = None
    question: str | None = Field(default=None, min_length=1, max_length=2000)
    expected_answer: str | None = None
    source: str | None = None


class QuestionOut(BaseModel):
    """测评问题出参"""
    id: str
    group: GroupAllItem
    question: str
    expected_answer: str | None = None
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChunkOut(BaseModel):
    """关联chunk出参"""
    id: str
    content: str


class QuestionDetailOut(QuestionOut):
    """测评问题详情（含关联chunk）"""
    chunks: list[ChunkOut]


class QuestionListOut(BaseModel):
    """测评问题分页出参"""
    items: list[QuestionOut]
    total: int
    page: int
    page_size: int



class TaskCreate(BaseModel):
    """创建测评任务"""
    name: str = Field(min_length=1, max_length=200, description="任务名称")
    group_id: str = Field(..., description="所属组ID")
    knowledge_base_id: str = Field(min_length=1, description="知识库ID")
    question_ids: list[str] | None = Field(default=None, description="参与测评的问题ID列表，不传则使用该组下所有问题")
    model_config_id: str = Field(min_length=1, description="模型配置ID")


class TaskOut(BaseModel):
    """测评任务出参（模板配置，运行时状态见 EvaluationRun）"""
    id: str
    name: str
    group: GroupAllItem
    type: EvaluationTaskType
    knowledge_base: KnowledgeBaseOut
    total_questions: int
    question_ids: list[str] | None = None
    config: dict | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskListOut(BaseModel):
    """测评任务分页出参"""
    items: list[TaskOut]
    total: int
    page: int
    page_size: int

class ModelConfigOut(BaseModel):
    """模型配置出参"""
    id: str
    name: str
    provider: str


class RunOut(BaseModel):
    """测评运行出参"""
    id: str
    task_id: str
    type: EvaluationTaskType
    status: EvaluationTaskStatus
    knowledge_base: KnowledgeBaseOut
    total_questions: int
    completed_questions: int
    avg_recall: dict | None = None
    avg_mrr: Decimal | None = None
    avg_correctness: Decimal | None = None
    avg_faithfulness: Decimal | None = None
    config: dict | None = None
    error_message: str | None = None
    model: ModelConfigOut
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RunListOut(BaseModel):
    """测评运行分页出参"""
    items: list[RunOut]
    total: int
    page: int
    page_size: int



class ExecuteEvaluationRequest(BaseModel):
    """执行测评请求"""
    task_id: str = Field(min_length=1, description="测评任务ID")


class ExecuteEvaluationResponse(BaseModel):
    """执行测评响应"""
    task_id: str
    run_id: str
    queue_id: str


class ResultOut(BaseModel):
    """测评结果出参"""
    id: str
    run_id: str
    question_id: str
    answer: str
    status: EvaluationResultStatus
    mrr: Decimal | None = None
    correctness: Decimal | None = None
    faithfulness: Decimal | None = None
    retrieval_metrics: dict | None = None
    latency_ms: int | None = None
    trace_data: dict | None = None
    error_message: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ResultListOut(BaseModel):
    """结果列表出参"""
    items: list[ResultOut]
    page: int
    page_size: int
    total: int
