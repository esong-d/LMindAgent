import asyncio

from sentence_transformers import SentenceTransformer

from app.integrations.embedding_provider import OpenAICompatibleEmbeddingProvider


class EmbeddingsManager:
    """
    向量嵌入器,负责将文本转换为向量表示,以便进行向量检索和相似度计算

    目前支持两种嵌入方式:
        1. OpenAI的API, 使用OpenAI的API进行文本嵌入, 性能较好, 但需要网络请求和API密钥
        2. sentence_transformers的API, 轻量级别的模型适合本地部署, 但性能可能不如OpenAI的API
    """
    def __init__(self, model_name: str = None, api_key: str = None, api_base: str = None, vector_dim: int = 384):
        """
        初始化嵌入参数配置, 优先使用实例传入的参数, 也可方法中动态传入参数进行初始化

        可自定义配置嵌入模型名称、API密钥、API地址和向量维度, 以支持不同的嵌入模型和配置

        如果不配置, 这使用官方默认地址(https://api.openai.com/v1)和对应的密钥

        :params model_name: 嵌入模型名称, 可以在运行时动态切换模型和维度
        :params api_key: 嵌入模型API密钥, 默认为None, 如果为None, 则使用环境变量OPENAI_API_KEY
        :params api_base: 嵌入模型API地址, 默认为None, 如果为None, 则使用环境变量OPENAI_API_BASE
        :params vector_dim: 嵌入向量的维度, 默认为384, 需要与模型输出的维度一致

        """
        self.api_key = api_key
        self.api_base = api_base
        self.model_name = model_name
        self.vector_dim = vector_dim
        self.embeddings_model = None
        self.openai_embed_provider: OpenAICompatibleEmbeddingProvider | None = None
    
    async def init_openai_embed_model(
            self, model_name: str = "text-embedding-3-small", 
            api_key: str = None, 
            api_base: str = None, 
            vector_dim: int = 1536
        ) -> OpenAICompatibleEmbeddingProvider:
        """
        初始化OpenAI的嵌入模型, 可以在运行时动态切换模型和维度

        :params model_name: 嵌入模型名称, 默认为"text-embedding-3-small", 支持(text-embedding-3-small, text-embedding-3-large)

        :params vector_dim: 嵌入向量的维度, 默认为1536, 需要与模型输出的维度一致(small:1536, large:3072)
        
        :return: OpenAIEmbeddings实例
        """
        if self.api_key is None and api_key is None:
            raise ValueError("OpenAI API密钥不能为空, 请通过参数传入或在配置中设置")
        self.api_key = self.api_key or api_key

        if self.api_base is None and api_base is None:
            raise ValueError("OpenAI API Base URL不能为空, 请通过参数传入或在配置中设置")
        self.api_base = self.api_base or api_base

        if self.model_name is None and model_name is None:
            raise ValueError("OpenAI嵌入模型名称不能为空, 请通过参数传入或在配置中设置")
        self.model_name = self.model_name or model_name

        if self.api_base:
            self.openai_embed_provider: OpenAICompatibleEmbeddingProvider = OpenAICompatibleEmbeddingProvider(
                model=self.model_name,
                api_key=self.api_key,
                api_base=self.api_base,
                timeout_seconds=60.0
            )
        else:
            # 使用openai官方默认地址, 兼容环境变量配置
            self.openai_embed_provider: OpenAICompatibleEmbeddingProvider = OpenAICompatibleEmbeddingProvider(
                model=self.model_name,
                api_key=self.api_key,
                timeout_seconds=60.0
            )
        self.vector_dim = vector_dim

        return self.openai_embed_provider

    async def init_sentence_transformers_model(
            self, 
            model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
        ) -> SentenceTransformer:
        """
        初始化sentence_transformers的嵌入模型, 可以在运行时动态切换模型

        :params model_name: 嵌入模型名称, 默认为"all-MiniLM-L6-v2", 这是一个轻量级别的模型, 输出维度为384
        
        :return: SentenceTransformer实例
        """
        self.embeddings_model: SentenceTransformer = SentenceTransformer(model_name)
        self.vector_dim = self.embeddings_model.get_sentence_embedding_dimension()

        return self.embeddings_model
    
    async def embed_with_openai_model(self, texts: list[str] | str) -> list[float]:
        """
        使用OpenAI的API进行文本嵌入, 性能较好, 但需要网络请求和API密钥
        将文本转换为向量表示

        :param texts: 要嵌入的文本列表, 可以是字符串列表或Document对象列表

        :return: 嵌入向量列表
        """
        if self.openai_embed_provider is None:
            await self.init_openai_embed_model()
        
        vector = await self.openai_embed_provider.aembed_documents(texts)
        return vector

    async def embed_with_sentence_transformers(self, texts: list[str] | str) -> list[float]:
        """
        使用sentence_transformers的API进行文本嵌入,
        轻量级别的模型适合本地部署, 但性能可能不如OpenAI的API
        将文本转换为向量表示

        :param texts: 待嵌入的文本列表, 可以是字符串列表或Document对象列表

        :return: 嵌入后的向量列表
        """
        if self.embeddings_model is None:
            await self.init_sentence_transformers_model()

        loop = asyncio.get_running_loop()
        vector = await loop.run_in_executor(
            None,
            self.embeddings_model.encode,
            texts,
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        return vector


