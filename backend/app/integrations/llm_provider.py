

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.errors import AppError

@dataclass
class ChatResult:
    id: str = ""
    content: str = ""
    additional_kwargs: dict[str, Any] = field(default_factory=dict)
    response_metadata: dict[str, Any] = field(default_factory=dict)
    tool_calls: list = field(default_factory=list)
    invalid_tool_calls: list = field(default_factory=list)
    usage_metadata: dict[str, Any] = field(default_factory=dict)

@dataclass 
class OutPut:
    id: str = ""
    content: str = ""
    additional_kwargs: dict[str, Any] = field(default_factory=dict)
    response_metadata: dict[str, Any] = field(default_factory=dict)
    tool_calls: list = field(default_factory=list)
    invalid_tool_calls: list = field(default_factory=list)
    usage_metadata: dict[str, Any] = field(default_factory=dict)
    tool_call_chunks: list = field(default_factory=list)

@dataclass 
class StreamChunk:
    content: str = ""
    

@dataclass
class StreamResult:
    data: OutPut
    event: str = ""
    run_id: str = ""
    name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    parent_ids: list = field(default_factory=list)


class LLMProvider(ABC):
    @abstractmethod
    async def achat(self, messages: list[dict[str, Any]] | str) -> ChatResult:
        raise NotImplementedError

    @abstractmethod
    async def astream_chat(self, messages: list[dict[str, Any]] | str) -> AsyncIterator[StreamChunk | StreamResult]:
        raise NotImplementedError


class OpenAICompatibleLLMProvider(LLMProvider):
    def __init__(self, *, base_url: str, api_key: str, model: str, timeout_seconds: float):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def achat(self, messages: list[dict[str, Any]] | str) -> ChatResult:
        try:
            from langchain_openai import ChatOpenAI
        except Exception:
            raise AppError(code="langchain_missing", message="LangChain is not installed", status_code=500)
        
        llm = ChatOpenAI(
            model=self.model,
            openai_api_key=self.api_key or None,
            openai_api_base=self.base_url or None,
            request_timeout=self.timeout_seconds,
        )

        out = await llm.ainvoke(messages)
        
        return ChatResult(
            content=out.content,
            additional_kwargs=out.additional_kwargs,
            response_metadata=out.response_metadata,
            id=out.id,
            tool_calls=out.tool_calls,
            invalid_tool_calls=out.invalid_tool_calls,
            usage_metadata=out.usage_metadata,
        )

    async def astream_chat(
        self, 
        messages: list[dict[str, Any]] | str
    ) -> AsyncIterator[StreamChunk | StreamResult]:
        try:
            from langchain_openai import ChatOpenAI
        except Exception:
            raise AppError(code="langchain_missing", message="LangChain is not installed", status_code=500)
        
        llm = ChatOpenAI(
            model=self.model,
            openai_api_key=self.api_key or None,
            openai_api_base=self.base_url or None,
            request_timeout=self.timeout_seconds,
            streaming=True,
        )
        
        async for chunk in llm.astream_events(messages):
            event = chunk.get("event", "on_chat_model_stream")
            if event == "on_chat_model_stream":
                yield StreamChunk(chunk["data"]["chunk"].content)
            elif event == "on_chat_model_end":
                yield StreamResult(
                    event=event,
                    data=OutPut(
                        content=chunk["data"]["output"].content,
                        additional_kwargs=chunk["data"]["output"].additional_kwargs,
                        response_metadata=chunk["data"]["output"].response_metadata,
                        id=chunk["data"]["output"].id,
                        tool_calls=chunk["data"]["output"].tool_calls,
                        invalid_tool_calls=chunk["data"]["output"].invalid_tool_calls,
                        usage_metadata=chunk["data"]["output"].usage_metadata,
                        tool_call_chunks=chunk["data"]["output"].tool_call_chunks,
                    ),
                    run_id=chunk["run_id"],
                    name=chunk["name"],
                    metadata=chunk["metadata"],
                    parent_ids=chunk["parent_ids"],
                )

                
class DeepSeekLLMProvider(LLMProvider):
    def __init__(self, *, base_url: str, api_key: str, model: str, timeout_seconds: float):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
    
    async def achat(self, messages: list[dict[str, Any]] | str) -> ChatResult:
        try:
            from langchain_deepseek import ChatDeepSeek
        except Exception:
            raise AppError(code="langchain_missing", message="LangChain is not installed", status_code=500)

        llm = ChatDeepSeek(
            model=self.model,
            api_key=self.api_key or None,
            base_url=self.base_url or None,
            timeout=self.timeout_seconds,
        )

        out = await llm.ainvoke(messages)

        return ChatResult(
            content=out.content,
            additional_kwargs=out.additional_kwargs,
            response_metadata=out.response_metadata,
            id=out.id,
            tool_calls=out.tool_calls,
            invalid_tool_calls=out.invalid_tool_calls,
            usage_metadata=out.usage_metadata,
        )

    async def astream_chat(self, messages: list[dict[str, Any]] | str) -> AsyncIterator[StreamChunk | StreamResult]:
        try:
            from langchain_deepseek import ChatDeepSeek
        except Exception:
            raise AppError(code="langchain_missing", message="LangChain is not installed", status_code=500)

        llm = ChatDeepSeek(
            model=self.model,
            api_key=self.api_key or None,
            base_url=self.base_url or None,
            timeout=self.timeout_seconds,
            streaming=True,
        )

        async for chunk in llm.astream_events(messages):
            event = chunk.get("event", "on_chat_model_stream")
            if event == "on_chat_model_stream":
                yield StreamChunk(chunk["data"]["chunk"].content)
            elif event == "on_chat_model_end":
                yield StreamResult(
                    event=event,
                    data=OutPut(
                        content=chunk["data"]["output"].content,
                        additional_kwargs=chunk["data"]["output"].additional_kwargs,
                        response_metadata=chunk["data"]["output"].response_metadata,
                        id=chunk["data"]["output"].id,
                        tool_calls=chunk["data"]["output"].tool_calls,
                        invalid_tool_calls=chunk["data"]["output"].invalid_tool_calls,
                        usage_metadata=chunk["data"]["output"].usage_metadata,
                        tool_call_chunks=chunk["data"]["output"].tool_call_chunks,
                    ),
                    run_id=chunk["run_id"],
                    name=chunk["name"],
                    metadata=chunk["metadata"],
                    parent_ids=chunk["parent_ids"],
                )


def get_llm_provider(
    provider: Literal['openai', 'deepseek', 'anthropic', 'ollama'],
    api_base: str,
    api_key: str,
    model: str,
    timeout_seconds: float,
) -> LLMProvider:
    if provider == "openai":
        return OpenAICompatibleLLMProvider(
            base_url=api_base,
            api_key=api_key,
            model=model or "",
            timeout_seconds=timeout_seconds,
        )
    elif provider == "deepseek":
        return DeepSeekLLMProvider(
            base_url=api_base,
            api_key=api_key,
            model=model or "",
            timeout_seconds=timeout_seconds,
        )
    
    elif provider == "anthropic":
        raise ValueError(f"{provider} is not supported yet")

    elif provider == "ollama":
        raise ValueError(f"{provider} is not supported yet")

    else:
        raise ValueError(f"Unknown provider: {provider}")

