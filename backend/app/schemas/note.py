from datetime import datetime

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    knowledge_base_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(default="")
    tags_json: list[str] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = None
    tags_json: list[str] | None = None


class NoteOut(BaseModel):
    id: str
    knowledge_base_id: str
    user_id: int
    title: str
    content: str
    tags_json: list[str]
    created_at: datetime 

    class Config:
        from_attributes = True


class NoteOveriew(BaseModel):
    id: str
    knowledge_base_id: str
    user_id: int
    title: str
    tags_json: list[str]
    created_at: datetime 
    class Config:
        from_attributes = True