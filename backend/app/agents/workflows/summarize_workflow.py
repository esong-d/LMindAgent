

from sqlalchemy.ext.asyncio import AsyncSession



class SummarizeWorkflow:
    """
    摘要工作流, 负责处理基于文档的摘要任务,
    包括检索相关文档、构建提示词、调用LLM生成摘要
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self, *, user_id: int, document_id: str) -> str:
        ...
