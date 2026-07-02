from langchain_core.tools import tool



@tool("get_weather", description="获取天气信息")
async def get_weather() -> str:
    return "今天天气很好！阳光明媚，适合出门游玩。"
