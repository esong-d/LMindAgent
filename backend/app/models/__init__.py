

def init_model():
    from app.models.user import User
    from app.models.conversation import Conversation
    from app.models.document import Document
    from app.models.document_chunk import DocumentChunk
    from app.models.knowledge_base import KnowledgeBase
    from app.models.mcp import McpServer, McpServerBinding, McpTool, McpResource, McpCallLog
    from app.models.message_tools import MessageTools
    from app.models.message import Message
    from app.models.model_config import ModelConfig
    from app.models.note import Note
    from app.models.task import Task

    from app.models.evaluation import (
        EvaluationGroup,
        EvaluationQuestion,
        EvaluationQuestionChunk,
        EvaluationTask,
        EvaluationResult
    )
    
