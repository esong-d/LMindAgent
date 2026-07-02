from datetime import datetime, timezone

from sqlalchemy import func, or_, select, update

from app.db.repositories._base import BaseRepository
from app.models.document_chunk import DocumentChunk


class ChunkRepository(BaseRepository):
    async def list_by_document(self, *, user_id: int, document_id: str) -> list[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.user_id == user_id, 
                DocumentChunk.document_id == document_id,
                DocumentChunk.deleted_at.is_(None),
            )
            .order_by(DocumentChunk.chunk_index.asc())
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def get_by_ids(self, *, user_id: int, chunk_ids: list[str]) -> list[DocumentChunk]:
        if not chunk_ids:
            return []
        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.user_id == user_id, 
                DocumentChunk.id.in_(chunk_ids),
                DocumentChunk.deleted_at.is_(None),
            )
        )
        res = await self.db.scalars(stmt)
        rows = list(res.all())
        by_id = {c.id: c for c in rows}
        return [by_id[cid] for cid in chunk_ids if cid in by_id]
    
    async def count_by_kb(self, user_id: int):
        stmt = (
            select(DocumentChunk.document_id.label("document_id"), func.count(DocumentChunk.id).label("count"))
            .where(
                DocumentChunk.user_id == user_id,
                DocumentChunk.deleted_at.is_(None),
            )
            .group_by(DocumentChunk.document_id)
        )
        res = await self.db.execute(stmt)
        return list(res.all())

    async def bulk_create(self, *, chunks: list[DocumentChunk]) -> None:
        self.db.add_all(chunks)
        await self.commit()

    async def delete_by_document(self, *, user_id: int, document_id: str) -> int:
        # 软删除
        stmt = (
            update(DocumentChunk)
            .where(
                DocumentChunk.user_id == user_id, 
                DocumentChunk.document_id == document_id,
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self.db.execute(stmt)
        await self.commit()
        return result.rowcount

    async def list_by_kb(self, *, user_id: int, knowledge_base_id: str, limit: int = 2000) -> list[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.user_id == user_id, 
                DocumentChunk.knowledge_base_id == knowledge_base_id,
                DocumentChunk.deleted_at.is_(None),
            )
            .order_by(DocumentChunk.created_at.desc())
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_similar_chunks(
        self, *, user_id: int, query_embedding: list[float], top_k: int = 10, knowledge_base_id: str | None = None
    ) -> list[DocumentChunk]:
        """向量检索"""
        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.user_id == user_id,
                DocumentChunk.deleted_at.is_(None),
            )
        )
        if knowledge_base_id:
            stmt = stmt.where(DocumentChunk.knowledge_base_id == knowledge_base_id)
        
        stmt = stmt.order_by(
            DocumentChunk.embedding.cosine_distance(query_embedding)
        ).limit(top_k)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
    
    async def get_chunks_by_full_text(
        self, user_id: int, querys: list[str], knowledge_base_id: str | None = None, limit: int = 50
    ):
        """全文检索"""
        if not querys:
            return []
        
        tsquery_exprs = [func.plainto_tsquery("simple", q) for q in querys]

        match_expr = or_(*[
            DocumentChunk.search_vector.op("@@")(tsq)
            for tsq in tsquery_exprs
        ])
        rank_expr = func.greatest(*[
            func.ts_rank_cd(DocumentChunk.search_vector, tsq)
            for tsq in tsquery_exprs
        ])
        conditions = [
            match_expr,
            DocumentChunk.user_id == user_id,
            DocumentChunk.deleted_at.is_(None),
        ]

        if knowledge_base_id:
            conditions.append(DocumentChunk.knowledge_base_id == knowledge_base_id)
        
        stmt = (
            select(
                DocumentChunk.id,
                DocumentChunk.content,
                DocumentChunk.document_id,
                DocumentChunk.knowledge_base_id,
                DocumentChunk.chunk_index,
                DocumentChunk.section_title,
                DocumentChunk.page_number,
                DocumentChunk.metadata_json,
                rank_expr.label("rank")
            )
            .where(*conditions)
            .order_by(rank_expr.desc())
            .limit(limit)
        )
        rows = await self.db.execute(stmt)
        return rows.all()
    
    async def get_chunk_count(
        self, 
        user_id: int, 
        knowledge_base_id: str | None = None,
        document_id: str | None = None
    ) -> int:
        stmt = (
            select(func.count(DocumentChunk.id))
            .where(
                DocumentChunk.user_id == user_id,
                DocumentChunk.deleted_at.is_(None),
            )
        )
        if knowledge_base_id:
            stmt = stmt.where(DocumentChunk.knowledge_base_id == knowledge_base_id)
        if document_id: 
            stmt = stmt.where(DocumentChunk.document_id == document_id)
        
        res = await self.db.execute(stmt)
        return res.scalars().first()