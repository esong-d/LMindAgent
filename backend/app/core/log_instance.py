from loguru import logger
#
# 分类 Logger
#

app_logger = logger.bind(module="app")

http_logger = logger.bind(module="http")

db_logger = logger.bind(module="db")

rag_logger = logger.bind(module="rag")

llm_logger = logger.bind(module="llm")

redis_logger = logger.bind(module="redis")

worker_logger = logger.bind(module="worker")