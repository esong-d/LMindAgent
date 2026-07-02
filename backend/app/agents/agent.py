

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.workflows.qa_workflow import QAWorkflow


class KnowledgeAgent:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.qa = QAWorkflow(db)

    async def answer(
        self, 
        user_id: int, 
        query: str,
        knowledge_base_id: str | None = None,
        conversation_id: str | None = None
    ) -> dict[str, Any]:
        return await self.qa.chat(
            user_id=user_id, 
            query=query, 
            knowledge_base_id=knowledge_base_id,
            conversation_id=conversation_id,
        )

    async def stream_answer(
        self, 
        user_id: int, 
        query: str,
        knowledge_base_id: str | None = None,
        conversation_id: str | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        async for event in self.qa.stream(
            user_id=user_id, query=query, knowledge_base_id=knowledge_base_id, conversation_id=conversation_id
        ):
            yield event
