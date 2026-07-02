

from typing import Any

from pydantic import BaseModel


class DocumentUpload(BaseModel):
    knowledge_base_id: str
    file_id: str
    new_filename: str
    original_filename: str
    file_type: str
    file_size: int
    


class DocumentOut(BaseModel):
    id: str
    knowledge_base_id: str
    user_id: int
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: str
    error_message: str
    metadata_json: dict[str, Any]
    processing_started_at: Any | None = None
    processing_completed_at: Any | None = None
    created_at: Any | None = None
    updated_at: Any | None = None

    class Config:
        from_attributes = True
