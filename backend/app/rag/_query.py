from functools import wraps
import json
from typing import Literal

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.prompts import ChatPromptTemplate

from app.integrations.llm_provider import ChatResult, LLMProvider
from app.integrations.model_config_provider import ModelConfigProvider
from app.agents.prompts.query_prompt import (
    build_keywords_prompt,
    build_query_check_prompt,
    build_rewrite_query_prompt,
    build_multi_query_prompt,
    build_route_prompt
)
from app.core.log_instance import llm_logger


class QueryHandler:
    """
    处理用户的输入

    1.判断输入是否正常提问 

    2.改写提问query 

    3.多问题query
    
    """
    def __init__(
            self, 
            db: AsyncSession,
            min_len: int = 2,
            max_len: int = 8192,
        ):
        self.db: AsyncSession = db
        self.min_len: int = min_len
        self.max_len: int = max_len
        self.model_config_provider: ModelConfigProvider = ModelConfigProvider(db)
    
    async def check_query(self, query: str, user_id: int) -> str | None:
        """
        规范化并校验 query, 返回可用的 query; 无效则返回 None
        """
        if not isinstance(query, str):
            return None

        if not self._is_basic_valid(query):
            return None
        
        if not await self._is_question(query, user_id):
            return None

        return query
    
    async def rewrite_query(self, query: str, user_id: int) -> list[str]:
        """
        改写用户输入的query
        """
        llm_provider: LLMProvider = await self.model_config_provider.build_llm_provider(user_id)
        query_rewrite_prompt: ChatPromptTemplate = build_rewrite_query_prompt()
        response: ChatResult = await llm_provider.achat(query_rewrite_prompt.format(query=query))
        
        return response.content
    
    async def multi_query(self, query: str, history: list, user_id: int) -> tuple[list, int]:
        """
        多问题query拆分
        """
        llm_provider: LLMProvider = await self.model_config_provider.build_llm_provider(user_id)
        query_multi_prompt: ChatPromptTemplate = build_multi_query_prompt()
        response: ChatResult = await llm_provider.achat(query_multi_prompt.format_messages(
            history=history,
            query=query
        ))
        try:
            data = json.loads(response.content)
        except Exception as e:
            raise e
        
        return data, len(data)
    
    def _is_basic_valid(self, query: str) -> bool:
        """
        query 是否有效
        """
        if not query:
            return False
        
        # 判断query长度, openai 最大长度为8192, 最小长度为20
        if len(query) < self.min_len or len(query) > self.max_len:
            return False
        
        return True
    
    async def _is_question(self, query: str, user_id: int) -> bool:
        """
        query 是否为问题
        """
        llm_provider: LLMProvider = await self.model_config_provider.build_llm_provider(user_id)
        query_check_prompt: ChatPromptTemplate = build_query_check_prompt()
        response: ChatResult = await llm_provider.achat(query_check_prompt.format(query=query))
        if response.content == "False":
            return False
        
        return True


def retry(max_cnt: int = 3):
    """
    重试装饰器
    """
    def decorator(func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            for i in range(max_cnt):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    llm_logger.error(f"{func.__name__} retry {i + 1}/{max_cnt}: {e}")
                    if i == max_cnt - 1:
                        raise e
                    continue      
            
        return wrapper
    
    return decorator

class RouterOutSchema(BaseModel):
    route: Literal["rag", "chitchat"]  

class RewriteQueryOutSchema(BaseModel):
    queries: list[str]

class KeywordsOutSchema(BaseModel):
    keywords: list[str]

class QueryManager:
    """
    路由节点处理
    rag, chitchat
    """
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
    
    @retry(max_cnt=3)
    async def get_route(self, query: str, history: list) -> str:
        route_prompt: ChatPromptTemplate = build_route_prompt()
        res = await self.llm.ainvoke(route_prompt.format_messages(
            query=query,
            history=history,
        ))
        return res.content
            
    @retry(max_cnt=3)
    async def get_rewrite_query(self, query: str, history: list) -> str:
        rewrite_query_prompt: ChatPromptTemplate = build_rewrite_query_prompt()
        res = await self.llm.ainvoke(
            rewrite_query_prompt.format_messages(
                query=query, 
                history=history
            )
        )
        return json.loads(res.content)

    
    @retry(max_cnt=3)
    async def get_keywords(self, query: str | list[str]) -> list:
        keywords_prompt: ChatPromptTemplate = build_keywords_prompt()
        res = await self.llm.ainvoke(keywords_prompt.format(query=",".join(query)))
        return json.loads(res.content)
