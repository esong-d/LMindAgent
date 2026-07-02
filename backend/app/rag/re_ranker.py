
import asyncio

from FlagEmbedding import FlagReranker
from langchain_core.documents import Document



class RerankerManager:
    """
    重排序器,负责对检索到的文档进行重新排序,以提高问答的准确性
    """
    def __init__(
        self, 
        model: str = "BAAI/bge-reranker-base", 
        use_fp16: bool = True
    ):
        """
        初始化重排序器, 可以在运行时动态切换模型
        BaAI/bge-reranker-large: 2.5G模型大小, 输出维度为768
        BAAI/bge-reranker-v2-m3: 2.5G模型大小, 输出维度为768
        BAAI/bge-reranker-base: 1.10G模型大小, 输出维度为768

        :params model: 重排序模型名称, 默认为"BAAI/bge-reranker-base", 这是一个基于BERT的模型, 输出维度为768
        :params use_fp16: 是否使用FP16精度, 默认为True, 可以提高性能但可能降低部分模型的准确性
        :params **kwargs: 关键字参数

        """
        self.model_name = model
        self.use_fp16 = use_fp16
        self.re_rank_model: FlagReranker | None = None
        self.lock = asyncio.Lock()
    
    async def init_model(
        self, 
        model: str = None, 
        use_fp16: bool = True,
        **kwargs
    ) -> FlagReranker:
        """初始化重排序模型, 可以在运行时动态切换模型"""
        model = self.model_name or model
        use_fp16 = self.use_fp16 or use_fp16

        async with self.lock:
            if self.re_rank_model is None:
                loop = asyncio.get_event_loop()
                self.re_rank_model = await loop.run_in_executor(
                    None,
                    self._init_model,
                    model,
                    use_fp16,
                    **kwargs
                )
        
        return self.re_rank_model
    
    def _init_model(self, model: str, use_fp16: bool, **kwargs) -> None:
        return FlagReranker(
            model_name_or_path=model,
            use_fp16=use_fp16,
            **kwargs
        )
    
    async def re_rank(
        self,
        query: str,
        documents: list[Document] | list[str] | str,
        **kwargs
    ) -> list[float]:
        """
        对检索到的文档进行重新排序, 返回每个文档的相关性得分

        :param query: 用户查询文本
        :param documents: 待重排序的文档列表, 每个文档包含文本内容和元数据, 可以是Document对象列表或字符串列表
        :param **kwargs: 关键字参数, 可以传递给重排序模型的其他参数

        :return: 每个文档的相关性得分列表, 与输入文档列表顺序对应
        """
        if self.re_rank_model is None:
            await self.init_model()
        
        pairs = await self._format_query(query, documents)
        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            None,
            self.re_rank_model.compute_score,
            pairs,
            **kwargs
        )
        return scores
    
    async def _format_query(
        self, 
        query: str, 
        documents: list[Document] | list[str] | str
    ) -> list[tuple[str, str]]:
        """
        将查询和文档格式化为字符串
        :param query: 查询
        :param documents: 文档
        :return: 格式化后的字符串
        """
        format_result = []
        if isinstance(documents, str):
            format_result.append([query, documents])
        
        if isinstance(documents, list):
            for doc in documents:
                if isinstance(doc, Document):
                    format_result.append([query, doc.page_content])
                elif isinstance(doc, str):
                    format_result.append([query, doc])
        
        return format_result
        
