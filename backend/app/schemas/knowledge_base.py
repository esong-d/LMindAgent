

from typing import Any

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=1024)
    settings_json: dict[str, Any] = Field(default_factory=dict)


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1024)
    settings_json: dict[str, Any] | None = None


class KnowledgeBaseOut(BaseModel):
    id: str
    user_id: int
    name: str
    description: str
    settings_json: dict[str, Any]

    class Config:
        from_attributes = True
