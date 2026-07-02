

from typing import Any

from pydantic import BaseModel, Field


class ModelConfigCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    provider: str
    base_url: str
    api_key: str = Field(default="")
    chat_model: str = Field(default="")
    is_default: bool = Field(default=False)


class ModelConfigUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    provider: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    chat_model: str | None = None
    is_default: bool | None = None


class ModelConfigOut(BaseModel):
    id: str
    user_id: int
    name: str
    provider: str
    base_url: str
    chat_model: str
    is_default: bool
    status: str
    last_tested_at: Any | None = None
    last_test_result_json: dict[str, Any]
    api_key_masked: str = Field(default="")

    class Config:
        from_attributes = True

