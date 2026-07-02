import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time 



async def main():
    print("开始加载数据...")
    try:
        from rag.loader import LoaderManager
        from rag.splitter import Splitters
    except Exception as e:
        print(f"导入依赖失败: {e!r}")
        raise

    loader = LoaderManager()
    splitter = Splitters(chunk_size=50, chunk_overlap=10)

    # text = """这是一个测试文本。它包含多个句子，用于测试文本分割功能。文本分割器应该能够正确地将这个文本分割成适合模型处理的小块，同时保留上下文信息。"""
    # with open("./uploads/test.txt", "r", encoding="utf-8") as f:
    #     text = f.read()
    # print("原始文本:", text)
    # t = time.time()
    # text_load = await loader.text_load(path="./uploads/test.txt", encoding="utf-8")
    # # print(text_load)
    # print("加载文本耗时:", time.time() - t)
    # documents = await splitter.split_text(texts=[doc.page_content for doc in text_load])
    # # print(documents)
    # print("分词耗时:", time.time() - t)

    pdf_path = "./uploads/test.pdf"
    print("PDF路径:", pdf_path)
    t = time.time() 
    pdf_load = await asyncio.wait_for(loader.pdf_load(path=pdf_path), timeout=120)
    print("加载PDF耗时:", time.time() - t)
    print("加载PDF文档:", pdf_load)
    pdf_documents = await splitter.split_text(
        texts=[doc.page_content for doc in pdf_load],
        metadatas=[doc.metadata for doc in pdf_load]
    )
    print("PDF分词耗时:", time.time() - t)
    print(pdf_documents)

    # t = time.time()
    # csv_load = await loader.csv_load(path="./uploads/test.csv")
    # print(csv_load)
    # csv_documents = await splitter.split_text(texts=[doc.page_content for doc in csv_load])
    # print(csv_documents)
    # print("加载CSV耗时:", time.time() - t)

    # t = time.time()
    # md_load = await loader.markdown_load(path="./uploads/test.md")
    # print(md_load)
    # print("加载Markdown耗时:", time.time() - t)
    # md_documents = await splitter.split_text(texts=[doc.page_content for doc in md_load])
    # print(md_documents)
    # print("加载Markdown耗时:", time.time() - t)


if __name__ == "__main__":
    asyncio.run(main())
