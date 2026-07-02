import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio


from rag.re_ranker import RerankerManager

async def main():
    query = "中国的首都是哪里？"
    documents = [
        "中国的首都是北京。",
        "中国的首都是上海。",
        "这里是一些无关的文本。",
        "这里就是首都",
        "首都是一个国家的政治中心。",
        "中国是一个国家。",
        "首都是美国的华盛顿特区。",
        "中国的首都是广州。",
    ]
    print("Query:", query)
    print("Documents:", documents)

    reranker = RerankerManager(model="BAAI/bge-reranker-base", use_fp16=True)
    scores = await reranker.re_rank(query, documents)
    print(scores)

    print(sorted(zip(documents, scores), key=lambda x: x[1], reverse=True))


if __name__ == "__main__":
    asyncio.run(main())
