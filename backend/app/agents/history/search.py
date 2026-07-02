from sqlalchemy.ext.asyncio import AsyncSession
from langchain.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from app.db.repositories.message_repository import MessageRepository
from app.models.message import Message



async def search_history(
    db: AsyncSession, 
    user_id: int, 
    conversation_id: str, 
    limit: int = 6
) -> list[Message]:
    """
    搜索历史
    保留最近三轮对话历史
    
    Args:
        db (AsyncSession): 数据库连接
        user_id (int): 用户id
        conversation_id (str): 会话id
        limit (int, optional): 最大返回数量. Defaults to 20.

    Returns:
        list[Message]: 历史消息列表
    
    """
    message_repo = MessageRepository(db)
    result = await message_repo.recent_message(
            user_id=user_id, 
            conversation_id=conversation_id,
            limit=limit
        )

    result = _remove_duplicate(result)

    return _format_message(result)


def _format_message(messages: list[Message]):
    result = []
    for msg in messages:
        if msg.role == "user":
            result.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            result.append(AIMessage(content=msg.content))
        elif msg.role == "system":
            result.append(SystemMessage(content=msg.content))
        elif msg.role == "tool":
            result.append(ToolMessage(content=msg.content, tool_call_id=getattr(msg, "tool_call_id", "")))
        else:
            result.append(AIMessage(content=msg.content))

    return result

# 去重
def _remove_duplicate(messages: list[Message]):
    result = []
    exists = []
    for msg in messages:
        if msg.content not in exists:
            exists.append(msg.content)
            result.append(msg)
    
    return result
