

from typing import Any

from langchain_core.documents import Document


# 引用生成器,负责将文档转换为引用格式，以便在问答中提供给模型使用

def documents_to_sources(docs: list[Document]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for d in docs:
        m = d.metadata or {}
        sources.append(
            {
                "chunk_id": m.get("chunk_id", ""),
                "document_id": m.get("document_id", ""),
                "content": d.page_content,
                "score": float(m.get("score", 0.0) or 0.0),
                "page_number": m.get("page_number"),
                "section_title": m.get("section_title", ""),
                "metadata": m.get("metadata", {}) or {},
            }
        )
    return sources
