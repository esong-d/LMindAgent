

from pydantic import BaseModel, Field


class ChatReq(BaseModel):
    query: str = Field(min_length=1, max_length=8192)
    conversation_id: str | None = Field(default=None)
    knowledge_base_id: str | None = Field(default=None)


class ChatResp(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    sources: list[dict]
