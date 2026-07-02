

from collections import defaultdict

from langchain_core.documents import Document
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.db.repositories.chunk_repository import ChunkRepository
from app.integrations.model_config_provider import ModelConfigProvider
from app.models.document_chunk import DocumentChunk
from app.rag.embeddings import EmbeddingsManager

settings = get_settings()


class VectorRetriever:
    """
    基于向量的检索器
    负责从知识库中检索与查询相关的文档分块,使用向量相似度计算来排序结果
    """
    def __init__(
        self, 
        db: AsyncSession, 
        top_k: int = 30,
    ) -> None:
        """
        初始化向量检索器

        :param db: 数据库会话对象
        :param top_k: 最多返回的文档分块数量, 默认检索50

        """
        self.db: AsyncSession = db
        self.embedding_provider: EmbeddingsManager = EmbeddingsManager()
        self.model_config_provider = ModelConfigProvider(db)
        self.chunk_repo = ChunkRepository(self.db)
        self.top_k: int = top_k

    async def retrieve_with_embed(self, user_id: int, query_embeddings: list[float], knowledge_base_id: str | None = None) -> list[Document]:
        """
        根据查询文本向量检索相关的文档分块
        优先使用配置中的top_k配置, 如果未配置则使用默认值30

        :param query_embedding: 查询向量
        :param knowledge_base_id: 知识库ID

        :return: 与查询相关的文档分块列表, 每个分块包含文本内容和元数据
        """

        # 2. 从数据库中检索与查询向量相似的文档分块
        if knowledge_base_id:
            # 知识库中检索
            retrieved_chunks = await self.chunk_repo.get_similar_chunks(
                user_id=user_id,
                knowledge_base_id=knowledge_base_id,
                query_embedding=query_embeddings,
                top_k=settings.retrieval_default_top_k or self.top_k
            )
        else:
            # 全局检索
            retrieved_chunks = await self.chunk_repo.get_similar_chunks(
                user_id=user_id,
                query_embedding=query_embeddings,
                top_k=settings.retrieval_default_top_k or self.top_k
            )

        # 3. 将检索到的分块转换为Document对象列表
        return await self._format_documents(retrieved_chunks)
    
    async def retrieve_with_full_text(self, user_id: int, querys: list[str], knowledge_base_id: str | None = None) -> list[Document]:
        """
        根据查询文本检索相关的文档分块
        优先使用配置中的top_k配置, 如果未配置则使用默认值30

        :param query: 查询文本
        :param knowledge_base_id: 知识库ID

        :return: 与查询相关的文档分块列表, 每个分块包含文本内容和元数据
        """
        retrieved_chunks = await self.chunk_repo.get_chunks_by_full_text(
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            querys=querys,
            limit=settings.retrieval_default_top_k or self.top_k
        )

        return await self._format_documents(retrieved_chunks)
    
    async def _format_documents(self, document_chunks: list[DocumentChunk]) -> list[Document]:
        return [
            Document(
                page_content=chunk.content,
                metadata={
                    "document_chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "section_title": chunk.section_title,
                    "page_number": chunk.page_number,
                    **chunk.metadata_json
                }
            )
            for chunk in document_chunks
        ]


async def embed_retrieve(
    queries: list[str],
    embed_queries: list[list[float]],
    session_factory: async_sessionmaker,
    user_id: int,
    knowledge_base_id: str | None = None
) -> list[Document]:
    """
    向量检索

    :param queries: 查询文本
    :param embed_queries: 查询向量
    :param session_factory: 数据库会话工厂
    :param user_id: 用户ID
    :param knowledge_base_id: 知识库ID
    :return: 检索结果
    """
    async with session_factory() as db:
        vector_docs_list = []
        vector_retriever = VectorRetriever(db)
        for _query_embed, _query in zip(embed_queries, queries):
            query_retrieve_list = await vector_retriever.retrieve_with_embed(
                user_id=user_id, 
                query_embeddings=_query_embed, 
                knowledge_base_id=knowledge_base_id
            )
            vector_docs_list += query_retrieve_list

    return vector_docs_list


async def bm25_retrieve(
    keywords: list[str],
    session_factory: async_sessionmaker,
    user_id: int,
    knowledge_base_id: str | None = None
) -> list[Document]:
    """
    BM25检索

    :param keywords: 查询关键词
    :param session_factory: 数据库会话工厂
    :param user_id: 用户ID
    :param knowledge_base_id: 知识库ID
    :return: 检索结果
    """
    async with session_factory() as db:
        vector_retriever = VectorRetriever(db)
        bm25_docs_list = await vector_retriever.retrieve_with_full_text(
            user_id=user_id,
            querys=keywords,
            knowledge_base_id=knowledge_base_id
        )
    return bm25_docs_list


async def rrf_fusion(
    result_sets: list[list[Document]],
    source_items: list[str],
    k: int = 60,
) -> tuple[list[Document], list[dict]]:
    """
    RRF(倒数排序融合, 增强向量检索和BM25检索)

    RRF + rank tracing + score tracing

    :param result_sets: 检索结果集(包含向量检索和BM25检索等)
    :param source_item: 检索来源(vector/bm25), 与result_sets一一对应
    :param k: 排序参数

    :return: rrf_res, rrf_trace
    """

    scores = defaultdict(float)

    # 用于记录详细信息
    trace_map = defaultdict(lambda: {
        "chunk_id": None,
        "sources": []
    })

    docs_map = {}

    for docs, source_name in zip(result_sets, source_items):

        for rank, doc in enumerate(docs, start=1):
            chunk_id = doc.metadata["document_chunk_id"]

            rrf_score = 1 / (k + rank)

            scores[chunk_id] += rrf_score
            docs_map[chunk_id] = doc

            # 初始化
            trace_map[chunk_id]["chunk_id"] = chunk_id

            # 记录每个 source 的 rank + score
            trace_map[chunk_id]["sources"].append({
                "source": source_name,
                "rank": rank,
                "rrf_score": rrf_score
            })

    # 排序
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # 输出 doc
    rrf_res = [docs_map[chunk_id] for chunk_id, _ in ranked]

    # 输出 trace（关键增强）
    rrf_trace = []
    for chunk_id, score in ranked:
        rrf_trace.append({
            "chunk_id": chunk_id,
            "final_rrf_score": score,
            "sources": trace_map[chunk_id]["sources"]
        })

    return rrf_res, rrf_trace