
from langchain_core.tools import tool




@tool("search_knowledge_base")
async def search_knowledge_base(query: str) -> str:
    ...