

from dataclasses import asdict
import json
from collections.abc import AsyncIterator
from typing import Any
import uuid

from langchain.chat_models import init_chat_model
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.history.search import search_history
from app.agents.workflows.qa_graph_workflow import ConfigContext, build_graph
from app.api.deps import UserInfo
from app.core.errors import NotFoundError
from app.agents.agent import KnowledgeAgent
from app.core.security import AESCipher
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.message_repository import MessageRepository
from app.db.repositories.model_config_repository import ModelConfigRepository
from app.integrations.embedding_provider import make_embedding_provider
from app.integrations.llm_provider import StreamResult
from app.rag._query import QueryManager
from app.schemas.chat import ChatReq
from app.core.config import get_settings


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.conversations = ConversationRepository(db)
        self.messages = MessageRepository(db)
        self.agent = KnowledgeAgent(db)
        self.documents_repo = DocumentRepository(db)
        self.model_configs = ModelConfigRepository(db)
        self.settings = get_settings()

    def _sse(self, event: str, data: dict[str, Any]) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    async def _ensure_conversation(
        self, user_id: int, 
        query: str, 
        conversation_id: str | None = None, 
        knowledge_base_id: str | None = None
    ) -> ConversationRepository:
        if conversation_id:
            conv = await self.conversations.get_by_id(
                user_id=user_id, 
                conversation_id=conversation_id
            )
            if not conv:
                raise NotFoundError("Conversation not found")
            
            return conv
        
        title = (query[:50] + "…") if len(query) > 50 else query

        return await self.conversations.create(
            user_id=user_id,
            title=title, 
            knowledge_base_id=knowledge_base_id
        )

    async def chat(
        self,
        payload: ChatReq,
        current_user: UserInfo,
    ) -> dict[str, Any]:
        conv = await self._ensure_conversation(
            user_id=current_user.id, 
            conversation_id=payload.conversation_id, 
            query=payload.query, 
            knowledge_base_id=payload.knowledge_base_id
        )
        # 创建用户消息
        await self.messages.create(
            user_id=current_user.id,
            conversation_id=conv.id,
            role="user",
            message_type="text",
            content=payload.query,
            sources_json=[],
            metadata_json={},
        )

        agent_out = await self.agent.answer(
            user_id=current_user.id, 
            query=payload.query, 
            knowledge_base_id=payload.knowledge_base_id,
            conversation_id=conv.id,
        )
        sources = [msg.metadata for msg in agent_out["sources"]]
        answer = agent_out["answer"]
        # 创建ai消息
        assistant = await self.messages.create(
            user_id=current_user.id,
            conversation_id=conv.id,
            role="ai",
            message_type="text",
            content=answer,
            sources_json=sources,
            metadata_json={},
        )

        # 查询引用文档
        sources_details = await self.get_sources_details(current_user.id, sources)

        return {"conversation_id": conv.id, "message_id": assistant.id, "answer": answer, "sources": sources_details}

    async def stream_chat(
        self,
        *,
        user_id: int,
        query: str,
        knowledge_base_id: str | None = None,
        conversation_id: str | None = None,
    ) -> AsyncIterator[str]:
        conv = await self._ensure_conversation(
            user_id=user_id, 
            knowledge_base_id=knowledge_base_id, 
            conversation_id=conversation_id, 
            query=query
        )
        await self.messages.create(
            user_id=user_id,
            conversation_id=conv.id,
            role="user",
            message_type="text",
            content=query,
            sources_json=[],
            metadata_json={},
        )
        yield self._sse("message_start", {"conversation_id": conv.id})

        result: StreamResult | None = None
        sources: list[dict[str, Any]] = []
        sources_details: list[dict[str, Any]] = []

        async for event in self.agent.stream_answer(
            user_id=user_id, 
            knowledge_base_id=knowledge_base_id, 
            conversation_id=conv.id,
            query=query,
        ):
            etype = str(event.get("type") or "")
            if etype == "delta":
                delta = str(event.get("delta") or "")
                yield self._sse("message_delta", {"delta": delta})
                continue

            if etype == "result":
                result: StreamResult | None = event.get("data", "")
                continue

            if etype == "sources":
                sources = event.get("sources")
                if isinstance(sources, list):
                    # 查询引用文档
                    sources_details = await self.get_sources_details(user_id, sources)
                continue
        
        if result:
            assistant = await self.messages.create(
                user_id=user_id,
                conversation_id=conv.id,
                role="ai",
                message_type="text",
                content=result.data.content,
                sources_json=sources,
                metadata_json=asdict(result.data),
            )

            yield self._sse("sources", {"sources": sources_details})
            yield self._sse("message_done", {"conversation_id": conv.id, "message_id": assistant.id})

    
    async def get_sources_details(self, user_id: int, sources: list[dict[str, Any]]):
        # 查询引用文档
        documents_ids = list(set(s["document_id"] for s in sources))
        sources_details_list = await self.documents_repo.get_by_ids(user_id=user_id, document_ids=documents_ids)

        return [{"document_id": s.id, "original_filename": s.original_filename} for s in sources_details_list]

    async def stream_graph_chat(
        self,
        *,
        session_factory: async_sessionmaker,
        user_id: int,
        query: str,
        knowledge_base_id: str | None = None,
        conversation_id: str | None = None,
    ) -> AsyncIterator[str]:
        conv = await self._ensure_conversation(
            user_id=user_id, 
            knowledge_base_id=knowledge_base_id, 
            conversation_id=conversation_id, 
            query=query
        )
        await self.messages.create(
            user_id=user_id,
            conversation_id=conv.id,
            role="user",
            message_type="text",
            content=query,
            sources_json=[],
            metadata_json={},
        )
        yield self._sse("message_start", {"conversation_id": conv.id})
        # 用户模型配置
        cfg = await self.model_configs.get_default(user_id=user_id)
        if not cfg:
            raise NotFoundError("Model config not found")
        
        api_key = AESCipher(self.settings.aes_key_hex).decrypt(cfg.api_key_encrypted) if cfg.api_key_encrypted else ""
        # 初始化模型
        chat_model = init_chat_model(
            model=cfg.chat_model,
            model_provider=cfg.provider,
            api_key=api_key,
            base_url=cfg.base_url,
            streaming=True,
        )
        # 向量化模型
        embed_llm = await make_embedding_provider(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_api_base,
            model=self.settings.embedding_vector_model,
        )
        query_manager = QueryManager(chat_model)
        # 会话历史记录
        history_messages = await search_history(self.db, user_id, conversation_id)

        # 构建graph
        rag_graph = build_graph()
        async for event in rag_graph.astream(
            {
                "query": query, "route": None, "queries": [], "keywords": [],
                "vector_retrieval_docs": [], "bm25_retrieval_docs": [],
                "rrf_docs": [], "sources": [], "ranked_docs": [], "ranked_sources": [],
                "answer": None, "trace": [], "is_error": False, "error_msg": ""
            }, 
            config = {
                "configurable": {
                    "ctx": ConfigContext(
                        session_factory=session_factory,
                        knowledge_base_id=knowledge_base_id,
                        user_id= user_id,
                        llm=chat_model,
                        embed_llm=embed_llm,
                        query_manager=query_manager,
                        history_messages=history_messages
                    ),
                    "thread_id": str(uuid.uuid4())
                }
            },
            stream_mode=["custom", "messages"]
        ):
            # print("event:", event)
            etype, edata = event
            if etype == "messages":
                if isinstance(edata, tuple):
                    data, answer_meta = edata
                    if answer_meta.get("langgraph_node") in ["chitchat_node", "generate_answer_node"]:
                        yield self._sse("messages", data.content)
                else:
                    yield self._sse("messages", edata.content)
                    
            elif etype == "custom":
                if edata.get("event", "") == "answer":
                    if edata.get("is_error", ""):
                        yield self._sse("messages", edata.get("message", ""))
                    
                    sources_details = []
                    res_source = edata.get("sources")
                    if res_source:
                        sources_details = await self.get_sources_details(user_id, res_source)
                    # 保存回答
                    assistant = await self.messages.create(
                        user_id=user_id,
                        conversation_id=conv.id,
                        role="ai",
                        message_type="text",
                        content=edata.get("message"),
                        sources_json=res_source,
                        metadata_json={},
                    )
                    yield self._sse("sources", {"sources": sources_details})
                    yield self._sse("message_done", {"conversation_id": conv.id, "message_id": assistant.id})
                else:
                    # 执行流程
                    yield self._sse(etype, edata)
            else:
                continue