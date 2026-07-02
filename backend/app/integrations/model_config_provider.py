

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import AESCipher
from app.core.errors import NotFoundError
from app.db.repositories.model_config_repository import ModelConfigRepository
from app.integrations.embedding_provider import EmbeddingProvider, OpenAICompatibleEmbeddingProvider, SentenceTransformerEmbeddingProvider
from app.integrations.llm_provider import DeepSeekLLMProvider, LLMProvider, OpenAICompatibleLLMProvider, get_llm_provider


settings = get_settings()

class ModelConfigProvider:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model_configs = ModelConfigRepository(db)

    async def build_llm_provider(self, user_id: int, model_config_id: str) -> LLMProvider:
        """
        获取知识库的LLM提供者, 用户配置, 从数据库读取配置
        """
        cfg = await self.model_configs.get_by_id(user_id=user_id, model_config_id=model_config_id)
        if not cfg:
            raise NotFoundError("Model config not found")
        
        api_key = AESCipher(settings.aes_key_hex).decrypt(cfg.api_key_encrypted) if cfg.api_key_encrypted else ""
        return get_llm_provider(
            provider=cfg.provider,
            model=cfg.chat_model,
            api_key=api_key,
            api_base=cfg.base_url,
            timeout_seconds=settings.llm_request_timeout_seconds,
        )
    
    @staticmethod
    async def build_embedding_provider() -> EmbeddingProvider:
        """
        获取嵌入模型提供者, 默认配置openai
        """
        return OpenAICompatibleEmbeddingProvider(
            model=settings.embedding_vector_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
            timeout_seconds=settings.llm_request_timeout_seconds,
        )
