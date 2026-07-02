

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

class KnowledgeBase(BaseModel):
    id: Optional[str | None] = ""
    name:  Optional[str | None] = ""

class Document(BaseModel):
    id:  Optional[str | None] = ""
    filename:  Optional[str | None] = ""

class TaskOut(BaseModel):
    id: str
    user_id: int
    knowledge_base: KnowledgeBase
    document: Document
    type: str
    status: str
    progress: int
    retry_count: int
    input_json: dict[str, Any]
    output_json: dict[str, Any]
    error_message: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
