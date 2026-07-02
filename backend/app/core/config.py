

from functools import lru_cache
import os
from typing import Literal

from pydantic import AnyUrl, BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.log_instance import app_logger


class DatabaseOptions(BaseModel):
    echo: bool = Field(default=False, description="是否输出SQL日志")
    pool_recycle: int = Field(default=3600, description="连接池中连接的最大重用时间，单位为秒")
    pool_size: int = Field(default=20, description="连接池的大小")
    max_overflow: int = Field(default=10, description="连接池外的连接数量")
    pool_timeout: int = Field(default=30, description="获取连接时的超时时间，单位为秒")
    pool_pre_ping: bool = Field(default=True, description="启用连接池的ping功能")


class Settings(BaseSettings):
    # 文件配置路径
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 环境配置，支持开发、测试和生产环境
    environment: Literal["development", "test", "production"] = Field(default="development")
    
    # 项目基本信息
    project_name: str = Field(default="LMindAgent")
    project_version: str = Field(default="0.1.0")
    project_description: str = Field(default="LMindAgent")
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")
    openapi_url: str = Field(default="/openapi.json")

    logger_file_path: str = Field(default="./logs", description="日志文件路径")
    
    # API前缀
    api_prefix: str = Field(default="/api")

    # CORS配置
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
     
    # 数据库配置
    database_url: str = Field(default="sqlite+aiosqlite:///./lmind.db")
    database_options: DatabaseOptions = Field(default_factory=DatabaseOptions)

    # redis配置
    redis_url: str = Field(default="redis://localhost:6379/0")

    # JWT配置
    jwt_secret: str
    jwt_expire: int = Field(default=60*60*24*1)
    jwt_algorithm: str = Field(default="HS256")

    # JWT过期时间，单位为秒
    refresh_token_expire_seconds: int = Field(default=60 * 60 * 24)
    access_token_expire_seconds: int = Field(default=60 * 60 * 24)

    # 加密配置
    encryption_key: str = Field(default="", description="加密密钥")

    # AES加密配置
    aes_key_hex: str = Field(default="", description="用于加密敏感信息的AES密钥，必须是32字节（64个十六进制字符）的十六进制字符串") 

    # 存储配置
    storage_backend: Literal["local"] = Field(default="local")
    storage_local_dir: str = Field(default="./uploads")

    # 上传配置
    max_upload_mb: int = Field(default=50, description="最大上传文件大小, 单位为MB")
    allowed_upload_mime_types: list[str] = Field(
        default_factory=lambda: [
            "text/plain",
            "text/markdown",
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
    )

    # 默认的公共URL，用于生成访问链接等场景。如果未设置，将使用安全的默认值。
    public_base_url: str = Field(default="")

    # LLM配置
    llm_default_base_url: AnyUrl = Field(default="https://api.openai.com/v1")
    llm_request_timeout_seconds: float = Field(default=60.0)

    # 向量Embedding配置
    openai_api_base: str = Field(default="https://api.openai.com/v1")
    openai_api_key: str = Field(default="")
    embedding_vector_model: str = Field(default="text-embedding-3-small")
    embedding_vector_dim: int = Field(default=1536)
    

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def validate_openai_api_key(cls, v: str) -> str:
        """验证OpenAI API密钥的格式, 如果不符合格式要求则抛出异常"""
        if not v and cls.embedding_vector_model in [
            "text-embedding-3-small", 
            "text-embedding-3-large", 
            "text-embedding-ada-002"
        ]:
            raise ValueError("OpenAI向量嵌入模型需要设置OpenAI API密钥")
        
        if not v: return v

        if not v.startswith("sk-"):
            raise ValueError("OpenAI API密钥格式不正确")
        
        return v

    # 检索默认的top_k值
    retrieval_default_top_k: int = Field(default=8)

    # 重排配置
    RERANKER_MODEL_NAME: str = Field(default="BAAI/bge-base-en-v1.5")
    RERANKER_USE_FP16: bool = Field(default=True)
    RERANKER_TOP_K: int = Field(default=10)

    # langsmith
    langsmith_tracing: str = Field(default="false")
    langsmith_endpoint: str = Field(default="")
    langsmith_api_key: str = Field(default="")
    langsmith_project: str = Field(default="")


    # 文档最大处理次数
    max_retry_times: int = Field(default=3)

    def masked_secret(self, value: str) -> str:
        """密文化密钥显示前3位和后4位, 中间部分用******代替"""
        if not value:
            return ""
        if len(value) <= 8:
            return "****"
        return value[:8] + "**********" + value[-4:]

    def safe_base_url_host(self, url: AnyUrl | str) -> str:
        """安全地解析URL的主机部分, 如果解析失败则返回空字符串"""
        try:
            parsed = AnyUrl(url) if isinstance(url, str) else url
            return parsed.host or ""
        except Exception:
            return ""


def init_langsmith():
    settings = get_settings()

    # 配置langsmith
    os.environ["LANGSMITH_TRACING"] = settings.langsmith_tracing
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project

    app_logger.info("Langsmith 配置完成")


@lru_cache
def get_settings() -> Settings:
    return Settings()
