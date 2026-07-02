

from sqlalchemy.ext.asyncio import AsyncSession


class ResearchWorkflow:
    """
    研究工作流, 负责处理基于文献资料的研究任务,
    包括检索相关文献、构建提示词、调用LLM生成研究报告等步骤
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    def run(self, *, user_id: int, knowledge_base_id: str, query: str) -> dict:
        return {"report": "not implemented", "query": query, "knowledge_base_id": knowledge_base_id}
