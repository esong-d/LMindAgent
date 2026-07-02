import asyncio
from abc import ABC, abstractmethod

from app.core.errors import AppError
from app.core.config import get_settings

settings = get_settings()

class EmbeddingProvider(ABC):
    @abstractmethod
    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    async def aembed_query(self, text: str) -> list[float]:
        raise NotImplementedError


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """
    使用SentenceTransformer进行文本嵌入
    """
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", dim: int = 384):
        self.model_name = model_name
        self.embeddings_model = None
        self.vector_dim: int | None = None

    async def init_sentence_transformers_model(self):
        """
        初始化SentenceTransformer模型, 加载指定的预训练模型并获取向量维度信息

         :return: SentenceTransformer实例
        """
        from sentence_transformers import SentenceTransformer

        self.embeddings_model = SentenceTransformer(self.model_name)
        self.vector_dim = self.embeddings_model.get_sentence_embedding_dimension()

        return self.embeddings_model

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        if not self.embeddings_model:
            await self.init_sentence_transformers_model()
        
        return await asyncio.to_thread(
            self.embeddings_model.encode, 
            texts,
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=True
        )
    
    async def aembed_query(self, text: str) -> list[float]:
        if not self.embeddings_model:
            await self.init_sentence_transformers_model()
        
        return await asyncio.to_thread(
            self.embeddings_model.encode, 
            [text], 
            batch_size=1,
            normalize_embeddings=True,
            show_progress_bar=False
        )[0]


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    def __init__(self, *, base_url: str, api_key: str, model: str, timeout_seconds: float):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._aembed(texts)

    async def aembed_query(self, text: str) -> list[float]:
        return (await self._aembed([text]))[0]

    async def _aembed(self, inputs: list[str]) -> list[list[float]]:
        try:
            from langchain_openai import OpenAIEmbeddings
        except Exception:
            raise AppError(code="langchain_missing", message="LangChain is not installed", status_code=500)

        emb = OpenAIEmbeddings(
            model=self.model,
            openai_api_key=self.api_key or None,
            openai_api_base=self.base_url or None,
            request_timeout=self.timeout_seconds,
        )
        return await emb.aembed_documents(inputs)


async def make_embedding_provider(
        base_url: str, 
        api_key: str, 
        model: str
) -> EmbeddingProvider:
    """
    根据模型配置构建嵌入提供者, 如果是OpenAI兼容的云模型, 则返回OpenAICompatibleEmbeddingProvider, 否则返回SentenceTransformerEmbeddingProvider

    :param settings: 应用配置对象, 包含全局设置
    :param base_url: 模型API的基础URL, 用于云模型连接
    :param api_key: 模型API的密钥, 用于云模型认证
    :param model: 模型名称或标识, 用于确定使用哪个嵌入提供者

    :return: EmbeddingProvider实例
    """

    if model.startswith("text-embedding-") or model.startswith("text-search-"):
         return OpenAICompatibleEmbeddingProvider(
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout_seconds=settings.llm_request_timeout_seconds,
        )
    
    # 默认使用HashEmbeddingProvider作为回退方案, 维度可以根据需要调整
    return SentenceTransformerEmbeddingProvider()