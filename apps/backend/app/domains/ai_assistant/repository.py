from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def compute_cosine_similarity(db: Session, vec_a_json: str, vec_b_json: str) -> float | None:
    """Gọi trực tiếp Function T-SQL heritage.fn_CosineSimilarity dưới SQL Server."""
    stmt = text("SELECT heritage.fn_CosineSimilarity(:vec_a, :vec_b) AS similarity")
    result = db.execute(stmt, {"vec_a": vec_a_json, "vec_b": vec_b_json}).scalar()
    return float(result) if result is not None else None


def upsert_knowledge_chunk(
    db: Session,
    *,
    family_id: UUID,
    source_type: str,
    source_id: UUID,
    chunk_index: int,
    chunk_text: str,
    embedding_json: str,
    summary_text: str | None = None,
) -> dict[str, str]:
    """Gọi trực tiếp Stored Procedure heritage.usp_UpsertKnowledgeChunk dưới SQL Server."""
    stmt = text(
        """
        EXEC heritage.usp_UpsertKnowledgeChunk
            @FamilyId = :family_id,
            @SourceType = :source_type,
            @SourceId = :source_id,
            @ChunkIndex = :chunk_index,
            @ChunkText = :chunk_text,
            @EmbeddingJson = :embedding_json,
            @SummaryText = :summary_text
        """
    )
    row = (
        db.execute(
            stmt,
            {
                "family_id": str(family_id),
                "source_type": source_type,
                "source_id": str(source_id),
                "chunk_index": chunk_index,
                "chunk_text": chunk_text,
                "embedding_json": embedding_json,
                "summary_text": summary_text,
            },
        )
        .mappings()
        .one()
    )
    db.commit()
    return {"chunk_id": str(row["ChunkId"]), "action_taken": str(row["ActionTaken"])}
