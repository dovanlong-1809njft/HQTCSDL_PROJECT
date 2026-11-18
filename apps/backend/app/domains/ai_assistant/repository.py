from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def compute_cosine_similarity(db: Session, vec_a_json: str, vec_b_json: str) -> float | None:
    """Gọi trực tiếp Function T-SQL heritage.fn_CosineSimilarity dưới SQL Server."""
    stmt = text("SELECT heritage.fn_CosineSimilarity(:vec_a, :vec_b) AS similarity")
    result = db.execute(stmt, {"vec_a": vec_a_json, "vec_b": vec_b_json}).scalar()
    return float(result) if result is not None else None


def get_source_family(db: Session, source_type: str, source_id: UUID):
    """Kiểm tra FamilyId của bản ghi nguồn (post, heritage, member) kèm HOLDLOCK."""
    tables = {
        "post": "community.Posts",
        "heritage": "heritage.Items",
        "member": "genealogy.Members",
    }
    return db.execute(
        text(f"SELECT FamilyId FROM {tables[source_type]} WITH (HOLDLOCK) WHERE Id=:source_id"),
        {"source_id": str(source_id)},
    ).scalar_one_or_none()


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
    auto_commit: bool = True,
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
    if auto_commit:
        db.commit()
    return {"chunk_id": str(row["ChunkId"]), "action_taken": str(row["ActionTaken"])}


def clear_stale_knowledge_chunks(
    db: Session,
    *,
    source_type: str,
    source_id: UUID,
    keep_chunk_count: int,
    auto_commit: bool = True,
) -> int:
    """Gọi Stored Procedure heritage.usp_ClearStaleKnowledgeChunks để xóa các đoạn thừa."""
    stmt = text(
        """
        EXEC heritage.usp_ClearStaleKnowledgeChunks
            @SourceType = :source_type,
            @SourceId = :source_id,
            @KeepChunkCount = :keep_chunk_count
        """
    )
    row = (
        db.execute(
            stmt,
            {
                "source_type": source_type,
                "source_id": str(source_id),
                "keep_chunk_count": keep_chunk_count,
            },
        )
        .mappings()
        .one()
    )
    if auto_commit:
        db.commit()
    return int(row["DeletedChunkCount"] or 0)


def list_pending_knowledge_sources(
    db: Session,
    *,
    family_id: UUID | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Đọc danh sách bài viết (Posts) và di sản (Items) chưa có Vector từ view vw_PendingKnowledgeSources."""
    if family_id is not None:
        stmt = text(
            """
            SELECT TOP (:limit)
                [FamilyId], [SourceType], [SourceId], [Title], [RawContent], [SyncStatus], [CreatedAt]
            FROM [heritage].[vw_PendingKnowledgeSources]
            WHERE [FamilyId] = :family_id
            ORDER BY [CreatedAt] DESC
            """
        )
        rows = db.execute(stmt, {"limit": limit, "family_id": str(family_id)}).mappings().all()
    else:
        stmt = text(
            """
            SELECT TOP (:limit)
                [FamilyId], [SourceType], [SourceId], [Title], [RawContent], [SyncStatus], [CreatedAt]
            FROM [heritage].[vw_PendingKnowledgeSources]
            ORDER BY [CreatedAt] DESC
            """
        )
        rows = db.execute(stmt, {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]


def semantic_search_chunks(
    db: Session,
    *,
    family_id: UUID,
    query_vector_json: str,
    top_k: int = 3,
    min_score: float = 0.30,
    source_type: str | None = None,
) -> list[dict[str, Any]]:
    """Gọi trực tiếp Stored Procedure heritage.usp_SemanticSearch dưới SQL Server."""
    stmt = text(
        """
        EXEC heritage.usp_SemanticSearch
            @FamilyId = :family_id,
            @QueryVectorJson = :query_vector_json,
            @TopK = :top_k,
            @MinScore = :min_score,
            @SourceType = :source_type
        """
    )
    rows = (
        db.execute(
            stmt,
            {
                "family_id": str(family_id),
                "query_vector_json": query_vector_json,
                "top_k": top_k,
                "min_score": min_score,
                "source_type": source_type,
            },
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def find_relationship_path(
    db: Session,
    *,
    member_a_id: UUID,
    member_b_id: UUID,
) -> dict[str, Any] | None:
    """Gọi trực tiếp Stored Procedure genealogy.usp_FindRelationshipPath trên bảng bao đóng MemberClosure."""
    stmt = text(
        """
        EXEC genealogy.usp_FindRelationshipPath
            @MemberAId = :member_a_id,
            @MemberBId = :member_b_id
        """
    )
    row = (
        db.execute(
            stmt,
            {
                "member_a_id": str(member_a_id),
                "member_b_id": str(member_b_id),
            },
        )
        .mappings()
        .one_or_none()
    )
    db.commit()
    return dict(row) if row is not None else None


def save_ai_chat_message(
    db: Session,
    *,
    family_id: UUID,
    user_id: UUID,
    query_type: str,
    question: str,
    answer: str,
    referenced_source_ids_json: str | None = None,
) -> UUID | None:
    """Lưu lịch sử câu hỏi và câu trả lời của AI vào bảng reports.AiChatMessages."""
    stmt = text(
        """
        EXEC reports.usp_SaveAiChatMessage
            @FamilyId = :family_id,
            @UserId = :user_id,
            @QueryType = :query_type,
            @Question = :question,
            @Answer = :answer,
            @ReferencedSourceIds = :referenced_source_ids
        """
    )
    try:
        row = (
            db.execute(
                stmt,
                {
                    "family_id": str(family_id),
                    "user_id": str(user_id),
                    "query_type": query_type,
                    "question": question,
                    "answer": answer,
                    "referenced_source_ids": referenced_source_ids_json,
                },
            )
            .mappings()
            .one_or_none()
        )
        db.commit()
        return UUID(str(row["MessageId"])) if row and row.get("MessageId") else None
    except Exception:
        db.rollback()
        return None


def get_source_document(
    db: Session,
    *,
    family_id: UUID,
    source_type: str,
    source_id: UUID,
) -> dict[str, Any] | None:
    """Gọi trực tiếp Stored Procedure heritage.usp_GetKnowledgeSourceContent dưới SQL Server."""
    stmt = text(
        """
        EXEC heritage.usp_GetKnowledgeSourceContent
            @FamilyId = :family_id,
            @SourceType = :source_type,
            @SourceId = :source_id
        """
    )
    row = (
        db.execute(
            stmt,
            {
                "family_id": str(family_id),
                "source_type": source_type,
                "source_id": str(source_id),
            },
        )
        .mappings()
        .one_or_none()
    )
    return dict(row) if row is not None else None


def update_source_summary_in_chunks(
    db: Session,
    *,
    family_id: UUID,
    source_type: str,
    source_id: UUID,
    summary_text: str,
) -> int:
    """Gọi trực tiếp Stored Procedure heritage.usp_UpdateKnowledgeSummary dưới SQL Server."""
    stmt = text(
        """
        EXEC heritage.usp_UpdateKnowledgeSummary
            @FamilyId = :family_id,
            @SourceType = :source_type,
            @SourceId = :source_id,
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
                "summary_text": summary_text[:1000],
            },
        )
        .mappings()
        .one_or_none()
    )
    db.commit()
    return int(row["UpdatedChunkCount"] or 0) if row else 0


def recommend_related_family_members(
    db: Session,
    *,
    family_id: UUID,
    anchor_member_id: UUID | None = None,
    top_k: int = 4,
) -> list[dict[str, Any]]:
    """Gọi trực tiếp Stored Procedure genealogy.usp_RecommendRelatedMembers dưới SQL Server."""
    stmt = text(
        """
        EXEC genealogy.usp_RecommendRelatedMembers
            @FamilyId = :family_id,
            @AnchorMemberId = :anchor_member_id,
            @TopK = :top_k
        """
    )
    rows = (
        db.execute(
            stmt,
            {
                "family_id": str(family_id),
                "anchor_member_id": str(anchor_member_id) if anchor_member_id else None,
                "top_k": top_k,
            },
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]