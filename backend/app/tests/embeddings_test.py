import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.embeddings import EmbeddingsManager


async def main():
    # sentence_transformers的API, 轻量级别的模型适合本地部署, 但性能可能不如OpenAI的API
    embeddings_manager = EmbeddingsManager()
    text = [
        "中国的首都是北京。",
        "中国的首都是上海。",
        "这里是一些无关的文本。",
        "这里就是首都",
        "首都是一个国家的政治中心。",
        "中国是一个国家。",
        "首都是美国的华盛顿特区。",
        "中国的首都是广州。",
    ]
    embedding = await embeddings_manager.embed_with_sentence_transformers(text)
    print(embedding)
    print(len(embedding))

    # openai的API, 使用OpenAI的API进行文本嵌入, 性能较好, 但需要网络请求和API密钥
    # embeddings_manager = EmbeddingsManager(
    #     model_name="text-embedding-3-small",
    #     api_base="https://api.openai-proxy.org/v1",
    #     api_key="sk-7hWb3iPBChGbEO40NdwnX285M1rAJKyRe2rkgjmRcMH0piHH",
    #     vector_dim=1536,
    # )
    # text = [
    #     "This is a test sentence.",
    #     "Embeddings are useful for many NLP tasks.",
    #     "OpenAI provides powerful embedding models."
    # ]
    # vector_store = await embeddings_manager.embed_with_openai_model(text)
    # print(len(vector_store))
    # print(len(vector_store[0]))

if __name__ == "__main__":
    asyncio.run(main())