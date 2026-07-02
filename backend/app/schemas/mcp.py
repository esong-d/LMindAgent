

from typing import Any

from pydantic import BaseModel, Field


class McpServerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=1024)
    transport: str = Field(default="stdio")
    command: str = Field(default="")
    args_json: list[str] = Field(default_factory=list)
    url: str = Field(default="")
    env_json: dict[str, Any] = Field(default_factory=dict)
    scope: str = Field(default="global")
    is_enabled: bool = Field(default=True)


class McpServerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1024)
    transport: str | None = None
    command: str | None = None
    args_json: list[str] | None = None
    url: str | None = None
    env_json: dict[str, Any] | None = None
    scope: str | None = None
    is_enabled: bool | None = None


class McpServerOut(BaseModel):
    id: str
    user_id: int
    name: str
    description: str
    transport: str
    command: str
    args_json: list[str]
    url: str
    scope: str
    status: str
    is_enabled: bool
    last_error: str

    class Config:
        from_attributes = True


class McpToolOut(BaseModel):
    id: str
    user_id: int
    mcp_server_id: str
    name: str
    description: str
    input_schema_json: dict[str, Any]
    permission_policy: str
    is_enabled: bool

    class Config:
        from_attributes = True


class McpToolPermissionUpdate(BaseModel):
    permission_policy: str


class McpCallLogOut(BaseModel):
    id: str
    user_id: int
    conversation_id: str | None = None
    message_id: str | None = None
    mcp_server_id: str
    mcp_tool_id: str
    tool_name: str
    status: str
    arguments_json: dict[str, Any]
    result_summary: str
    error_message: str
    requires_approval: bool
    approved_by_user: bool

    class Config:
        from_attributes = True


class McpCallDecision(BaseModel):
    reason: str = Field(default="")
