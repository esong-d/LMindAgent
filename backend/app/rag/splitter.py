from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.documents import Document


class Splitters:
    """
    文本分割器,负责将长文本分割成适合模型处理的小块,支持重叠分块以保留上下文
    """
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 200) -> None:
        """初始化文本分割器

        :param chunk_size: 分块的最大字符数,默认500
        :param chunk_overlap: 分块之间的重叠字符数,默认200
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    async def split_text(self, texts: list[str] | str, metadatas: list[dict] | None = None) -> list[Document]:
        """
        使用递归字符文本分割器进行文本分割

        :param texts: 要分割的文本列表, 可以是字符串列表或字符串
        :param metadatas: 与文本对应的元数据列表

        :return: list[Document] 分割后的文档对象列表
        """
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, 
            chunk_overlap=self.chunk_overlap,
            add_start_index=True,        # 添加起始索引以便后续引用
            separators=[
                "\n\n", "\n", "。", "！", "？", "；", "，", " ", ".", ",", "!", "?", ";"
            ],                           # 自定义分隔符优先级高
        )
        if isinstance(texts, str):
            docs = splitter.create_documents([texts], metadatas=metadatas)
        else:
            docs = splitter.create_documents(texts, metadatas=metadatas)

        return docs

    async def split_text_with_token(self, *, text: list[str] | str, metadatas: list[dict] | None = None) -> list[Document]:
        """
        使用TokenTextSplitter进行文本分割

        :param text: 要分割的文本列表, 可以是字符串列表或字符串
        :param metadatas: 与文本对应的元数据列表

        :return: list[Document] 分割后的文档对象列表
        """
        from langchain_text_splitters import TokenTextSplitter

        splitter = TokenTextSplitter(
            chunk_size=self.chunk_size, 
            chunk_overlap=self.chunk_overlap,
            encoding_name="cl100k_base",      # 默认的编码名称, 适用于OpenAI的模型
            add_start_index=True,             # 添加起始索引以便后续引用
        )
        if isinstance(text, str):
            docs = splitter.create_documents([text], metadatas=metadatas)
        else:
            docs = splitter.create_documents(text, metadatas=metadatas)
        return docs

    async def split_text_semantic(self, *, text: list[str] | str, metadatas: list[dict] | None = None, api_key: str, api_base: str) -> list[Document]:
        """
        使用SemanticTextSplitter进行语义文本分割
        语义分割需要调用大模型进行文本理解, 需要提供OpenAI API的密钥和基础URL

        :param text: 要进行分割的文本列表, 可以是字符串列表或字符串
        :param metadatas: 与文本对应的元数据列表
        :param api_key: OpenAI API密钥
        :param api_base: OpenAI API基础URL

        :return: list[Document] 分割后的文档对象列表
        """
        from langchain_experimental.text_splitter import SemanticChunker
        from langchain_openai import OpenAIEmbeddings

        embeddings = OpenAIEmbeddings(
            api_key=api_key,
            api_base=api_base,
            model="text-embedding-3-large",   # 使用更小的模型以减少资源消耗
        )
        splitter = SemanticChunker(
            embeddings=embeddings,
            add_start_index=True,             # 添加起始索引以便后续引用
            breakpoint_threshold_amount=50.0,  # 设置断点阈值为0.5, 极低 -> 极高(高敏感分割)
        )
        if isinstance(text, str):
            docs = splitter.create_documents([text], metadatas=metadatas)
        else:
            docs = splitter.create_documents(text, metadatas=metadatas)
        return docs
