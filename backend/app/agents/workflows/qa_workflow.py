

from collections.abc import AsyncIterator
from dataclasses import asdict
import re
from typing import Any, Literal

import jieba
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.history.search import search_history
from app.core.config import get_settings
from app.db.repositories.message_repository import MessageRepository
from app.integrations.llm_provider import ChatResult, LLMProvider, StreamChunk, StreamResult
from app.integrations.model_config_provider import ModelConfigProvider
from app.agents.prompts.prompt import build_qa_prompt, format_document_context
from app.rag.retriever import VectorRetriever
from app.rag._query import QueryHandler
from app.core.rank import get_rank_manager

settings = get_settings()

class QAWorkflow:
    def __init__(self, db: AsyncSession):
        """
        知识问答工作流, 负责处理基于知识库的问答任务,
        包括检索相关知识、重排增强、构建提示词、调用LLM生成答案等步骤

        :param db: 数据库会话对象, 用于访问知识库和模型配置等数据

        """
        self.db = db
        self.retrieval: VectorRetriever = VectorRetriever(db)  
        self.model_config_provider = ModelConfigProvider(db)
        self.query_handler: QueryHandler = QueryHandler(db)
        self.messages = MessageRepository(db)
        self.reranker = get_rank_manager()
        self.top_k: int = settings.RERANKER_TOP_K

    async def chat(self, *, user_id: int, query: str, knowledge_base_id: str | None = None, conversation_id: str | None = None) -> dict[str, Any]:
        # 处理用户的输入(问题是否有效)
        check_query = await self.query_handler.check_query(query, user_id)
        if not check_query:
            return {"answer": "请输入一个有效的问题。", "sources": [], "tool_calls": []}
        query = check_query

        # 历史对话记录
        history_messages = await search_history(self.db, user_id, conversation_id)

        # 处理用户的输入(多问题query)
        history_query = [msg for msg in history_messages if msg.type == "human"]
        multi_query, query_cnt = await self.query_handler.multi_query(query, history_query, user_id)
        if query_cnt == 0:
            return {"answer": "请输入一个有效的问题。", "sources": [], "tool_calls": []}
        query = multi_query

        # 查询向量化
        embedding_provider = await self.model_config_provider.build_embedding_provider()
        query_embeddings_list = (await embedding_provider.aembed_documents(texts=multi_query))
        
        # 检索相关知识
        sources_docs_list = [] 
        for _query_embed in query_embeddings_list:
            query_retrieve = await self.retrieval.retrieve(
                user_id=user_id, query_embeddings=_query_embed, knowledge_base_id=knowledge_base_id
            )
            sources_docs_list += query_retrieve
        
        if not sources_docs_list:
            return {"answer": "暂无来源片段, 无法生成答案, 请先上传知识库, 提供相关资料。", "sources": [], "tool_calls": []}
        
        # 重排 reranker, 增强检索结果
        # sources_scores = await self.reranker.re_rank(query=query, documents=sources_docs)
        # sources_scores_list = sorted(zip(sources_docs, sources_scores), key=lambda x: x[1], reverse=True)
        # sources_res = [source for source, _ in sources_scores_list[:self.top_k]]
        
        # 构建prompt
        llm: LLMProvider = await self.model_config_provider.build_llm_provider(user_id=user_id)
        prompt = build_qa_prompt()
        msgs = prompt.format_messages(
            history=history_messages, 
            query=query, 
            context=format_document_context(sources=sources_docs_list)
        )
        
        # 调用LLM 生成答案
        result: ChatResult = await llm.achat([_msg_to_dict(m) for m in msgs])

        return {"answer": result.content, "sources": sources_docs_list, "tool_calls": result.tool_calls}

    async def stream(
        self, *, user_id: int, query: str, knowledge_base_id: str | None = None, conversation_id: str | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        try:
            # 处理用户的输入(判断输入是否正常提问)
            check_query = await self.query_handler.check_query(query, user_id)
            if not check_query:
                yield _msg_resp("delta", "请输入一个有效的问题。")
                yield _msg_resp("sources", [])
                return
            
            # 历史对话记录
            history_messages = await search_history(self.db, user_id, conversation_id)

            # 处理用户的输入(多问题query)
            history_query = [msg for msg in history_messages if msg.type == "human"]
            multi_query, query_cnt = await self.query_handler.multi_query(check_query, history_query, user_id)
            if query_cnt == 0:
                yield _msg_resp("delta", "请输入一个有效的问题。")
                yield _msg_resp("sources", [])
                return  
            
            # 原问题也加入多问题列表
            multi_query.append(query)

            # 查询向量化
            embedding_provider = await self.model_config_provider.build_embedding_provider()
            query_embeddings_list = (await embedding_provider.aembed_documents(texts=multi_query))
            
            # 检索相关知识(向量检索)
            sources_docs_retrieve_embed_list = [] 
            sources_docs_retrieve_embed_dict = {}
            for _query_embed, _query in zip(query_embeddings_list, multi_query):
                query_retrieve_list = await self.retrieval.retrieve_with_embed(
                    user_id=user_id, query_embeddings=_query_embed, knowledge_base_id=knowledge_base_id
                )
                sources_docs_retrieve_embed_list += query_retrieve_list
                sources_docs_retrieve_embed_dict[_query] = query_retrieve_list
            
            # 检索相关知识(全文检索)
            sources_docs_retrieve_full_list = await self.retrieval.retrieve_with_full_text(
                user_id=user_id, querys=_tokenize(multi_query), knowledge_base_id=knowledge_base_id
            )

            if not sources_docs_retrieve_embed_list and not sources_docs_retrieve_full_list:
                yield _msg_resp("delta", "暂无来源片段, 无法生成答案, 请先上传知识库, 提供相关资料。")
                yield _msg_resp("sources", [])
                return

            # 重排 reranker, 增强检索结果
            import time
            t = time.time()
            sources_retrieve_merge = sources_docs_retrieve_embed_list + sources_docs_retrieve_full_list
            sources_retrieve_merge_res = []     # 去重
            for item in sources_retrieve_merge:
                if item not in sources_retrieve_merge_res:
                    sources_retrieve_merge_res.append(item)
            sources_scores = await self.reranker.re_rank(query=query, documents=sources_retrieve_merge_res)
            sources_scores_list = sorted(zip(sources_retrieve_merge_res, sources_scores), key=lambda x: x[1], reverse=True)
            sources_rerank_res = [(source, _score) for source, _score in sources_scores_list[:self.top_k]]
            print("rerank 耗时：", time.time() - t)

            # 构建prompt
            llm: LLMProvider = await self.model_config_provider.build_llm_provider(user_id=user_id)
            prompt = build_qa_prompt()
            msgs = prompt.format_messages(
                history=history_messages, 
                query=query, 
                context=format_document_context(sources=[_source for _source, _ in sources_rerank_res])
            )
            
            # 调用LLM  streaming 生成答案
            delta: StreamChunk | StreamResult | None = None
            result: StreamResult | None = None
            async for delta in llm.astream_chat([_msg_to_prompt(m) for m in msgs]):
                if isinstance(delta, StreamChunk):
                    yield _msg_resp("delta", delta.content)
                if isinstance(delta, StreamResult):
                    yield _msg_resp("result", delta)
                    result = delta
            
            sources_payload = [{**d.metadata, "score": _score} for d, _score in sources_rerank_res]
            if result and conversation_id:
                await self.messages.create(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    role="ai",
                    message_type="text",
                    content=result.data.content,
                    sources_json=sources_payload,
                    metadata_json=asdict(result.data),
                )

            # 最后返回引用来源
            yield _msg_resp("sources", sources_payload)
        
        except Exception as e:
            yield _msg_resp("delta", f"发生错误: {e}")
            yield _msg_resp("sources", [])
            return 


def _msg_to_dict(msg: Any) -> dict[str, Any]:
    role = getattr(msg, "type", "") or getattr(msg, "role", "") or "user"
    role_map = {
        "human": "human",
        "ai": "ai",
        "assistant": "assistant",
        "system": "system",
        "tool": "tool",
        "user": "user"
    }
    role = role_map.get(role, role)
    return {"role": role, "content": getattr(msg, "content", "") or ""}


def _msg_to_prompt(msg: Any) -> str:
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
    role = getattr(msg, "type", "") or getattr(msg, "role", "") or "user"
    role_map = {
        "human": "human",
        "ai": "ai",
        "assistant": "assistant",
        "system": "system",
        "tool": "tool",
        "user": "user"
    }
    role = role_map.get(role, role)
    if role in ["system"]:
        return SystemMessage(content=getattr(msg, "content", "") or "")
    elif role == "human":
        return HumanMessage(content=getattr(msg, "content", "") or "")
    elif role in ["assistant", "ai"]:
        return AIMessage(content=getattr(msg, "content", "") or "")
    # elif role == "tool":
    #     return ToolMessage(content=getattr(msg, "content", "") or "")
    else:
        return HumanMessage(content=getattr(msg, "content", "") or "")


def _msg_resp(
    type: Literal['delta', 'result', 'sources'],  # type: ignore
    data: list | dict | str | None = None
) -> dict[str, Any]:
    if type == "delta":
        return {"type": type, "delta": data}
    
    elif type == "result":
        return {"type": type, "data": data}
    
    elif type == "sources":
        return {"type": type, "sources": data}
    
    else:
        raise ValueError(f"Invalid type: {type}")


def _tokenize(text: str | list[str]) -> list[str]:
    # 去除标点符号和特殊字符
    if isinstance(text, list):
        text = " ".join(text)
    text = re.sub(r'\s+', '', text)
    return list(jieba.cut(text))
