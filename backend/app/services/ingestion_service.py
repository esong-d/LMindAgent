from __future__ import annotations

import hashlib
import os

import tiktoken
from pathlib import Path
import time
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.repositories.chunk_repository import ChunkRepository
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.task_repository import TaskRepository
from app.integrations.embedding_provider import EmbeddingProvider
from app.integrations.model_config_provider import ModelConfigProvider
from app.models.document_chunk import DocumentChunk
from app.models.document import DocumentStatus
from app.rag.splitter import Splitters
from app.rag.loader import LoaderManager
from app.rag.clean_text import clean_text

settings = get_settings()

if TYPE_CHECKING:
    from langchain_core.documents import Document


class IngestionService:

    async def ingest_document(
        self,
        *,
        user_id: int,
        document_id: str,
        task_id: str,
        chunk_size: int = 500,
        chunk_overlap: int = 150,
        session_maker: async_sessionmaker[AsyncSession],
    ) -> int:
        try:
            # 阶段 1: 读取信息, 设置初始状态
            async with session_maker() as session:
                documents_repo = DocumentRepository(session)
                tasks_repo = TaskRepository(session)

                await tasks_repo.set_result(
                    user_id=user_id, task_id=task_id,
                    input_json={"chunk_size": chunk_size, "chunk_overlap": chunk_overlap},
                )
                doc = await documents_repo.get_by_id(user_id=user_id, document_id=document_id)
                if not doc:
                    raise Exception(f"{doc.id} 文档不存在")

                # 在 session 关闭前提取后续需要的值, 避免访问已 detach 的 ORM 对象
                doc_filename = doc.filename
                doc_file_type = doc.file_type
                doc_kb_id = doc.knowledge_base_id
                doc_id = doc.id
                original_filename = doc.original_filename

                await documents_repo.set_status(
                    user_id=user_id, document_id=document_id, status=DocumentStatus.parsing,
                )

            # 阶段 2: 文档加载 (IO 密集, 不需要 session)
            load_start = time.perf_counter()
            loaded_docs = await _load_text(
                _get_storage_path(user_id=user_id, file_name=doc_filename), doc_file_type,
            )
            load_end = time.perf_counter()

            # 阶段 3: 文档清洗 (CPU 密集, 不需要 session)
            clean_documents: list[Document] = clean_text(loaded_docs)

            # 阶段 4: 开始分块
            async with session_maker() as session:
                documents_repo = DocumentRepository(session)
                await documents_repo.set_status(
                    user_id=user_id, document_id=document_id, status=DocumentStatus.chunking,
                )

            split_start = time.perf_counter()
            splitters = Splitters(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            documents_parts: list[Document] = await splitters.split_text(
                texts=[d.page_content for d in clean_documents],
                metadatas=[{**d.metadata, "original_filename": original_filename} for d in clean_documents],
            )
            split_end = time.perf_counter()
            
            # 阶段 5: 开始向量化
            async with session_maker() as session:
                documents_repo = DocumentRepository(session)
                tasks_repo = TaskRepository(session)
                await documents_repo.set_status(
                    user_id=user_id, document_id=document_id, status=DocumentStatus.embedding,
                )
                await tasks_repo.update_progress(user_id=user_id, task_id=task_id, progress=60)

            # 阶段 6: 创建向量
            embedding_provider: EmbeddingProvider = await ModelConfigProvider.build_embedding_provider()
            embeddings: list[list[float]] = (
                await embedding_provider.aembed_documents([part.page_content for part in documents_parts])
                if documents_parts
                else []
            )

            # 阶段 7: 构建分块对象
            new_chunks: list[DocumentChunk] = []
            for idx, (document_chunk, embedding) in enumerate(zip(documents_parts, embeddings)):
                content_hash = hashlib.sha256(document_chunk.page_content.encode("utf-8")).hexdigest()
                try:
                    enc = tiktoken.get_encoding("cl100k_base")
                    token_count = len(enc.encode(document_chunk.page_content))
                except Exception:
                    token_count = len(document_chunk.page_content)  # fallback
                new_chunks.append(
                    DocumentChunk(
                        user_id=user_id,
                        knowledge_base_id=doc_kb_id,
                        document_id=doc_id,
                        chunk_index=idx,
                        content=document_chunk.page_content,
                        content_hash=content_hash,
                        token_count=token_count,
                        page_number=document_chunk.metadata.get("page_number") if document_chunk.metadata else None,
                        section_title="",
                        metadata_json=document_chunk.metadata,
                        embedding=embedding,
                    )
                )

            # 阶段 8: 持久化结果
            async with session_maker() as session:
                documents_repo = DocumentRepository(session)
                chunks_repo = ChunkRepository(session)
                tasks_repo = TaskRepository(session)

                await tasks_repo.update_progress(user_id=user_id, task_id=task_id, progress=80)

                # 批量插入分块数据, 先删除原有分块再插入新分块
                await chunks_repo.delete_by_document(user_id=user_id, document_id=document_id)
                if new_chunks:
                    await chunks_repo.bulk_create(chunks=new_chunks)

                # 更新文档状态为就绪
                await documents_repo.set_status(
                    user_id=user_id, document_id=document_id, status=DocumentStatus.completed,
                )
                # 更新任务信息
                await tasks_repo.set_result(
                    user_id=user_id, task_id=task_id,
                    output_json={
                        "chunk_count": len(new_chunks),
                        "load_cost": f"{(load_end - load_start):.2f}",
                        "split_cost": f"{(split_end - split_start):.2f}",
                    },
                )

            return len(new_chunks)

        except Exception as e:
            raise e


async def _load_text(storage_path: str, file_type: str) -> list["Document"]:
    """
    Load text from storage path
    """
    if not os.path.exists(storage_path):
        raise AppError(code="file_not_found", message="Stored file not found", status_code=500)

    loader_manager = LoaderManager()
    if file_type == "text/plain":
        return await loader_manager.text_load(storage_path)

    if file_type == "text/markdown":
        return await loader_manager.markdown_load(storage_path)

    if file_type == "application/pdf":
        return await loader_manager.pdf_load(storage_path)

    if file_type == "text/csv":
        return await loader_manager.csv_load(storage_path)

    if file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return await loader_manager.docx_load(storage_path)

    if file_type == "application/vnd.ms-excel":
        return await loader_manager.excel_load(storage_path)

    raise AppError(code="unsupported_file_type", message="Unsupported file type", status_code=400, detail=file_type)


def _get_storage_path(user_id: int, file_name: str) -> Path:
    return Path(settings.storage_local_dir) / str(user_id) / file_name
