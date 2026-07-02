from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.documents import Document
     

class LoaderManager:
    """
    知识库加载器, 负责从数据库加载知识库相关的数据, 包括文档和分块等
    """
    def __init__(self): 
        ...
    
    async def get_encoding_type(self, path: str) -> str:
        """
        获取文件编码类型

        :param path: 文件路径

        :return: str 编码类型
        """
        from charset_normalizer import from_bytes

        def raw_load(path: str) -> bytes:
            with open(path, "rb") as f:
                raw = f.read()
            return raw
        
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(None, raw_load, path)

        result = from_bytes(raw).best()

        return result.encoding, result.language
    
    async def text_load(self, path: str, *args, **kwargs) -> list[Document]:
        """
        加载文本文件, 返回Document对象列表

        :param path: 文本文件路径
        :param args: 其他参数
        :param kwargs: 其他参数

        :return: list[Document] 文档对象列表
        """
        from langchain_community.document_loaders import TextLoader
        encoding, language = await self.get_encoding_type(path)
        text_load = TextLoader(path, encoding=encoding, *args, **kwargs)
        return [doc async for doc in text_load.alazy_load()]


    async def pdf_load(self, path: str, *args, **kwargs) -> list[Document]:
        """
        加载PDF文件, 返回Document对象列表

        :param path: PDF文件路径
        :param args: 其他参数
        :param kwargs: 其他参数

        :return: list[Document] 文档对象列表
        """
        from langchain_community.document_loaders import PyMuPDFLoader, PDFPlumberLoader

        try:
            pdf_loader = PDFPlumberLoader(path, extract_images=True, *args, **kwargs)
            result = [doc async for doc in pdf_loader.alazy_load()] 
        
        except Exception as e:
            pdf_loader = PyMuPDFLoader(path, images_inner_format='text', *args, **kwargs)
            result = [doc async for doc in pdf_loader.alazy_load()]

            # 无识别内容更换方式
            page_content = "".join([res.page_content for res in result])
            if not page_content or page_content == '':
                raise "识别内容为空"
        
        return result

    async def csv_load(self, path: str, *args, **kwargs) -> list[Document]:
        """
        加载CSV文件, 返回Document对象列表

        :param path: CSV文件路径
        :param args: 其他参数
        :param kwargs: 其他参数

        :return: list[Document] 文档对象列表
        """
        from langchain_community.document_loaders import UnstructuredCSVLoader

        csv_loader = UnstructuredCSVLoader(path, *args, **kwargs)
        return [doc async for doc in csv_loader.alazy_load()]

    async def markdown_load(self, path: str, *args, **kwargs) -> list[Document]:
        """
        加载Markdown文件, 返回Document对象列表

        :param path: Markdown文件路径
        :param args: 其他参数
        :param kwargs: 其他参数

        :return: list[Document] 文档对象列表
        """
        from langchain_community.document_loaders import UnstructuredMarkdownLoader

        markdown_loader = UnstructuredMarkdownLoader(path, *args, **kwargs)
        return [doc async for doc in markdown_loader.alazy_load()]
    
    async def docx_load(self, path: str, *args, **kwargs) -> list[Document]:
        """
        加载DOCX文件, 返回Document对象列表

        :param path: DOCX文件路径
        :param args: 其他参数
        :param kwargs: 其他参数

        :return: list[Document] 文档对象列表
        """
        from langchain_community.document_loaders import UnstructuredWordDocumentLoader
        docx_loader = UnstructuredWordDocumentLoader(path, *args, **kwargs)
        return [doc async for doc in docx_loader.alazy_load()]
    
    async def excel_load(self, path: str, *args, **kwargs) -> list[Document]:
        """
        加载EXCEL文件, 返回Document对象列表

        :param path: EXCEL文件路径
        :param args: 其他参数
        :param kwargs: 其他参数

        :return: list[Document] 文档对象列表
        """
        from langchain_community.document_loaders import UnstructuredExcelLoader
        excel_loader = UnstructuredExcelLoader(path, *args, **kwargs)
        return [doc async for doc in excel_loader.alazy_load()]


