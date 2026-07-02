from langchain_core.tools import tool


@tool("web_search")
async def web_search(query: str) -> str:
    ...