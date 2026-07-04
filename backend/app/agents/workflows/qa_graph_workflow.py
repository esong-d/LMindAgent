import asyncio
from dataclasses import dataclass
from operator import add
import time
from typing import Annotated, Any, Optional, TypedDict
from sqlalchemy.ext.asyncio import async_sessionmaker

from langsmith import traceable
from langgraph.config import get_stream_writer
from langgraph.graph import END, StateGraph
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from app.agents.prompts.prompt import build_qa_prompt, format_document_context
from app.agents.prompts.query_prompt import build_chitchat_prompt
from app.integrations.embedding_provider import EmbeddingProvider
from app.rag._query import QueryManager
from app.rag.retriever import bm25_retrieve, embed_retrieve, rrf_fusion
from app.core.config import get_settings
from app.core.rank import get_rank_manager

settings = get_settings()


class RagState(TypedDict):
    # user input
    query: str
    intent: Optional[str]

    # routing
    route: Optional[str]
    force_rag: bool      # 强制走 RAG 管线，跳过闲聊路由（测评场景使用）

    # multi query
    queries: list[str]
    keywords: list[str]

    # retrieval
    vector_retrieval_docs: list[dict[str, Any]]
    bm25_retrieval_docs: list[dict[str, Any]]
    rrf_docs: list[dict[str, Any]]
    sources: list[dict[str, Any]]

    # ranking
    ranked_docs: list[dict[Any, float]]
    ranked_sources: list[dict[str, Any]]

    # generation
    answer: Optional[str]

    # trace (UI + debug)
    trace: Annotated[list[dict[str, Any]], add]

    # error
    is_error: bool
    error_msg: str

@dataclass
class ConfigContext:
    """
    session_factory: async_sessionmaker

    knowledge_base_id: str | None

    user_id: int

    llm: BaseChatModel

    embed_llm: EmbeddingProvider

    query_manager: QueryManager
    """
    session_factory: async_sessionmaker
    knowledge_base_id: str | None
    user_id: int
    llm: BaseChatModel
    embed_llm: EmbeddingProvider
    query_manager: QueryManager
    history_messages: list[dict[str, Any]] | None


def _msg_to_prompt(msg: Any) -> SystemMessage | HumanMessage | AIMessage | ToolMessage:
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
    elif role == "tool":
        return ToolMessage(content=getattr(msg, "content", "") or "")
    else:
        return HumanMessage(content=getattr(msg, "content", "") or "")


def _format_custom_writer(event: str, node: str, message: str, **extra):
    try:
        writer = get_stream_writer()
        return writer({
            "event": event,
            "node": node,
            "message": message,
            **extra
        })
    except Exception as e:
        return None



@traceable(name="route_query")
async def route_query_node(state: RagState, config: RunnableConfig) -> RagState:
    """路由节点"""
    # 测评 / 强制 RAG 场景：跳过 LLM 路由
    if state.get("force_rag"):
        return {"intent": "rag", "route": "rewrite_query_node"}

    _format_custom_writer("status", "route_query_node", "正在分析意图...")
    
    cfg_ctx: ConfigContext = config["configurable"]["ctx"]
    try:
        res = await cfg_ctx.query_manager.get_route(state["query"], history=cfg_ctx.history_messages)
    except Exception as e:
        _format_custom_writer("status", "route_query_node", str(e), is_error=True)
        # 异常，路由降级处理
        return {"intent": "rag", "route": "error", "is_error": True, "error_msg": str(e)}
    
    _format_custom_writer("status", "route_query_node", "意图分析完成")
    if res == "chitchat":
        return {"intent": res, "route": "chitchat"}

    return {"intent": "rag", "route": "rewrite_query_node"}


@traceable(name="chitchat")
async def chitchat_node(state: RagState, config: RunnableConfig) -> RagState:
    """闲聊节点"""
    _format_custom_writer("status", "chitchat_node", "正在生成闲聊回答...")

    cfg_ctx: ConfigContext = config["configurable"]["ctx"]
    prompt = build_chitchat_prompt()
    msg = prompt.format_messages(query=state["query"], history=cfg_ctx.history_messages)
    res = await cfg_ctx.llm.ainvoke(msg)
    _format_custom_writer("answer", "chitchat_node", res.content)

    return {"answer": res.content}



@traceable(name="rewrite_query")
async def rewrite_query_node(state: RagState, config: RunnableConfig) -> RagState:
    """重写查询节点(改写, 多query, 关键词提取)"""
    _format_custom_writer("status", "rewrite_query_node", "正在改写查询...")

    cfg_ctx: ConfigContext = config["configurable"]["ctx"]
    res = await cfg_ctx.query_manager.get_rewrite_query(state["query"], cfg_ctx.history_messages)
    _format_custom_writer("status", "rewrite_query_node", f"查询改写完成, 查询分解结果: {','.join(res)}")

    return {"queries": res}


@traceable(name="keywords_extract")
async def keywords_extract_node(state: RagState, config: RunnableConfig) -> RagState:
    """关键词提取节点, 用于增强检索"""
    _format_custom_writer("status", "keywords_extract_node", "正在提取关键词...")

    cfg_ctx: ConfigContext = config["configurable"]["ctx"]
    if not state["queries"]:
        return {"keywords": []}
    
    res = await cfg_ctx.query_manager.get_keywords(state["queries"])
    _format_custom_writer("status", "keywords_extract_node", f"关键词提取完成, 关键词: {','.join(res)}")

    return {"keywords": res}


@traceable(name="retrieve")
async def retrieve_node(state: RagState, config: RunnableConfig) -> RagState:
    """检索节点"""
    _format_custom_writer("status", "retrieve_node", "正在检索文档...")

    queries = state["queries"]
    keywords  = state["keywords"]
    cfg_ctx: ConfigContext = config["configurable"]["ctx"]
    # 查询向量化
    query_embeddings_list = await cfg_ctx.embed_llm.aembed_documents(texts=queries)

    # 混合检索(hybrid search)
    vector_docs_list = [] 
    bm25_docs_list = []
    embed_retrieve_task = embed_retrieve(queries, query_embeddings_list, cfg_ctx.session_factory, cfg_ctx.user_id, cfg_ctx.knowledge_base_id)
    bm25_retrieve_task = bm25_retrieve(keywords, cfg_ctx.session_factory, cfg_ctx.user_id, cfg_ctx.knowledge_base_id)
    vector_docs_list, bm25_docs_list = await asyncio.gather(embed_retrieve_task, bm25_retrieve_task)
    
    # RRF
    rrf_input_data = [vector_docs_list, bm25_docs_list] if vector_docs_list or bm25_docs_list else []
    rrf_input_source = ["vector", "bm25"]
    rrf_total_docs, rrf_trace = await rrf_fusion(rrf_input_data, rrf_input_source) if rrf_input_data else ([], [])
    docs = rrf_total_docs[:30] if rrf_total_docs else []
    sources = []
    for doc in docs:
        source_chunk = {
            "document_id": doc.metadata["document_id"], 
            "document_chunk_id": doc.metadata["document_chunk_id"],
        }
        if source_chunk not in sources:
            sources.append(source_chunk)

    _format_custom_writer("status", "retrieve_node", f"""
        文档检索完成..., 
        向量检索 {len(vector_docs_list)} 个分片, 
        BM25检索 {len(bm25_docs_list)} 个分片,
        RRF融合 {len(rrf_total_docs)} 个分片
    """)

    retrieve_count = len(vector_docs_list) + len(bm25_docs_list)
    return {
        "vector_retrieval_docs": vector_docs_list,
        "bm25_retrieval_docs": bm25_docs_list,
        "rrf_docs": docs, 
        "sources": sources, 
        "trace": [{
            "retrieve_count": retrieve_count, 
            "vector_count": len(vector_docs_list), 
            "bm25_count": len(bm25_docs_list),
            "rrf_trace": rrf_trace,
        }]
    }


@traceable(name="rank")
async def ranked_node(state: RagState, config: RunnableConfig) -> RagState:
    """排序节点"""
    _format_custom_writer("status", "ranked_node", "正在重排检索结果...")

    query = state["query"]
    rrf_docs = state["rrf_docs"]
    start = time.perf_counter()
    sources_scores = await get_rank_manager().re_rank(query=query, documents=rrf_docs) if rrf_docs else []
    sources_scores_list = sorted(zip(rrf_docs, sources_scores), key=lambda x: x[1], reverse=True) if sources_scores else []
    sources_rerank_res = [(source, _score) for source, _score in sources_scores_list[:settings.RERANKER_TOP_K]] if sources_scores_list else []
    time_cost = time.perf_counter() - start

    _format_custom_writer(
        "status",
        "ranked_node",
        f"重排检索完成, 耗时: {time_cost:.2f}s, 重排结果: {len(sources_rerank_res)} 个分片"
    )

    doc: Document
    ranked_sources = []
    for doc, score in sources_rerank_res:
        ranked_sources.append({
            "document_id": doc.metadata["document_id"], 
            "document_chunk_id": doc.metadata["document_chunk_id"],
            "score": score
        })

    return {"ranked_docs": sources_rerank_res, "ranked_sources": ranked_sources}


@traceable(name="generate_answer")
async def generate_answer_node(state: RagState, config: RunnableConfig) -> RagState:
    """生成答案节点"""
    _format_custom_writer("status", "generate_answer_node", "正在生成答案...")

    cfg_ctx: ConfigContext = config["configurable"]["ctx"]
    chat_prompt = build_qa_prompt()
    msgs = chat_prompt.format_messages(
        history=cfg_ctx.history_messages, 
        query=state["query"], 
        context=format_document_context([doc for doc, _ in state["ranked_docs"]])
    )
    result = cfg_ctx.llm.astream_events(
        input=[_msg_to_prompt(m) for m in msgs],
        version="v2"
    )

    # 取最终回答
    answer = ""
    async for chunk in result:
        event = chunk.get("event", "on_chat_model_stream")
        if event == "on_chat_model_stream":
            continue
        if event == "on_chat_model_end":
            answer = chunk["data"]["output"].content

    _format_custom_writer("answer", "generate_answer_node", answer, sources=state["ranked_sources"])

    return {"answer": answer}



def build_graph():
    rag_graph = StateGraph(RagState)
    rag_graph.add_node("route_query_node", route_query_node)
    rag_graph.add_node("chitchat_node", chitchat_node)
    rag_graph.add_node("rewrite_query_node", rewrite_query_node)
    rag_graph.add_node("retrieve_node", retrieve_node)
    rag_graph.add_node("keywords_extract_node", keywords_extract_node)
    rag_graph.add_node("ranked_node", ranked_node)
    rag_graph.add_node("generate_answer_node", generate_answer_node)

    rag_graph.set_entry_point("route_query_node")
    rag_graph.add_conditional_edges(
        "route_query_node",
        lambda state: state["route"],
        {
            "rewrite_query_node": "rewrite_query_node",
            "chitchat": "chitchat_node",
            "error": END
        },
    )
    rag_graph.add_edge("chitchat_node", END)
    rag_graph.add_edge("rewrite_query_node", "keywords_extract_node")
    rag_graph.add_edge("keywords_extract_node", "retrieve_node")
    rag_graph.add_edge("retrieve_node", "ranked_node")
    rag_graph.add_edge("ranked_node", "generate_answer_node")
    rag_graph.add_edge("generate_answer_node", END)

    return rag_graph.compile()

