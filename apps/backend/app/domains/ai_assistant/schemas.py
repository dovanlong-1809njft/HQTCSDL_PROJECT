from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


# =====================================================================
# Tuần 1: Schemas kiểm thử Embedding, Cosine Similarity & Upsert đơn lẻ
# =====================================================================
class EmbeddingTestRequest(BaseModel):
    text: str = Field(
        default="Cụ tổ Nguyễn Văn Cẩn truyền nghề mộc cho con cháu tại Thạch Thất.",
        min_length=1,
        max_length=2000,
    )


class EmbeddingTestResponse(BaseModel):
    model: str
    dimensions: int
    preview_first_5: list[float]
    embedding_json: str


class CosineTestRequest(BaseModel):
    text_a: str = Field(
        default="Dòng họ mình làm nghề truyền thống gì?",
        min_length=1,
        max_length=2000,
    )
    text_b: str = Field(
        default="Nghề mộc theo họ Nguyễn Văn từ đời cụ tổ ở Thạch Thất.",
        min_length=1,
        max_length=2000,
    )


class CosineTestResponse(BaseModel):
    text_a: str
    text_b: str
    dimensions: int
    cosine_similarity: float | None


class UpsertChunkRequest(BaseModel):
    family_id: UUID = Field(default=UUID("22222222-2222-2222-2222-000000000001"))
    source_type: Literal["post", "heritage", "member"] = "heritage"
    source_id: UUID = Field(default=UUID("eeeeeeee-eeee-eeee-eeee-000000000004"))
    chunk_index: int = Field(default=0, ge=0)
    chunk_text: str = Field(
        default="Nghề mộc theo họ Nguyễn Văn từ đời cụ tổ. Cụ Cẩn học nghề năm mười bốn tuổi, sau truyền cho con cháu trong chi trưởng.",
        min_length=1,
        max_length=2000,
    )
    summary_text: str | None = Field(default=None, max_length=1000)


class UpsertChunkResponse(BaseModel):
    chunk_id: UUID
    action_taken: str
    dimensions: int


# =====================================================================
# Tuần 2 - Phần 1: Pipeline Cắt đoạn (Chunking 3-4 câu) & Vector hóa
# =====================================================================
class ChunkAndIndexRequest(BaseModel):
    family_id: UUID = Field(default=UUID("22222222-2222-2222-2222-000000000001"))
    source_type: Literal["post", "heritage", "member"] = "heritage"
    source_id: UUID = Field(default=UUID("eeeeeeee-eeee-eeee-eeee-000000000003"))
    title: str | None = Field(
        default="Chuyện cụ Cẩn dựng nhà thờ họ",
        max_length=300,
    )
    content: str = Field(
        default=(
            "Năm 1975 cụ Cẩn trở về làng, góp gỗ và công của cả chi trưởng lẫn chi thứ "
            "để dựng lại nhà thờ họ trên nền cũ. Công việc kéo dài hai mùa, tới giỗ tổ "
            "năm 1977 mới xong phần mái. Các cột chính được chạm khắc tinh xảo bởi chính "
            "tay các nghệ nhân trong dòng họ. Từ đó nhà thờ trở thành nơi hội tụ con cháu "
            "mỗi dịp giỗ tổ tháng Ba âm lịch."
        ),
        min_length=1,
        max_length=20000,
    )
    sentences_per_chunk: int = Field(default=3, ge=1, le=10)
    summary_text: str | None = Field(default=None, max_length=1000)


class IndexedChunkItem(BaseModel):
    chunk_id: UUID
    chunk_index: int
    chunk_text: str
    action_taken: str
    dimensions: int


class ChunkAndIndexResponse(BaseModel):
    family_id: UUID
    source_type: str
    source_id: UUID
    total_chunks: int
    deleted_stale_chunks: int
    chunks: list[IndexedChunkItem]


class SyncPendingRequest(BaseModel):
    family_id: UUID | None = Field(default=UUID("22222222-2222-2222-2222-000000000001"))
    sentences_per_chunk: int = Field(default=3, ge=1, le=10)
    limit: int = Field(default=20, ge=1, le=100)


class SyncedSourceSummary(BaseModel):
    source_type: str
    source_id: UUID
    title: str
    chunks_indexed: int


class SyncPendingResponse(BaseModel):
    sources_processed: int
    total_chunks_upserted: int
    items: list[SyncedSourceSummary]


# =====================================================================
# Tuần 2 - Phần 2 & 3: API Semantic Search (usp_SemanticSearch + RAG)
# =====================================================================
class SemanticSearchRequest(BaseModel):
    family_id: UUID = Field(default=UUID("22222222-2222-2222-2222-000000000001"))
    query: str = Field(
        default="Dòng họ Nguyễn Văn có nghề truyền thống gì và nhà thờ họ được dựng năm nào?",
        min_length=1,
        max_length=2000,
    )
    top_k: int = Field(default=3, ge=1, le=10)
    min_score: float = Field(default=0.30, ge=-1.0, le=1.0)
    source_type: Literal["post", "heritage", "member"] | None = Field(default=None)
    generate_answer: bool = Field(
        default=True,
        description="Nếu True, ghép Top-K đoạn văn vào Prompt và gọi Gemini trả lời tự nhiên.",
    )
    user_id: UUID | None = Field(default=UUID("11111111-1111-1111-1111-000000000001"))


class SemanticSearchHit(BaseModel):
    chunk_id: UUID
    family_id: UUID
    source_type: str
    source_id: UUID
    source_title: str
    chunk_index: int
    chunk_text: str
    summary_text: str | None = None
    similarity_score: float
    updated_at: datetime | None = None


class SemanticSearchResponse(BaseModel):
    family_id: UUID
    query: str
    top_k: int
    total_matches: int
    matches: list[SemanticSearchHit]
    ai_answer: str | None = None
    prompt_used: str | None = None
    chat_message_id: UUID | None = None


# =====================================================================
# Tuần 2 - Phần 4: Giải thích quan hệ họ hàng (usp_FindRelationshipPath)
# =====================================================================
class RelationshipExplainRequest(BaseModel):
    family_id: UUID = Field(default=UUID("22222222-2222-2222-2222-000000000001"))
    member_a_id: UUID = Field(
        default=UUID("44444444-4444-4444-4444-000000000001"),
        description="Mặc định: Cụ Nguyễn Văn Cẩn (1938)",
    )
    member_b_id: UUID = Field(
        default=UUID("44444444-4444-4444-4444-000000000005"),
        description="Mặc định: Cháu Nguyễn Văn Hùng (1995)",
    )
    question: str | None = Field(
        default="Hãy giải thích mối quan hệ họ hàng và cách xưng hô giữa hai thành viên này.",
        max_length=1000,
    )
    user_id: UUID | None = Field(default=UUID("11111111-1111-1111-1111-000000000001"))


class RelationshipPathData(BaseModel):
    member_a_id: UUID
    member_a_name: str
    member_a_birth_date: date | None = None
    member_a_branch_name: str | None = None
    member_b_id: UUID
    member_b_name: str
    member_b_birth_date: date | None = None
    member_b_branch_name: str | None = None
    relationship_category: str
    common_ancestor_id: UUID | None = None
    common_ancestor_name: str | None = None
    depth_from_ancestor_to_a: int | None = None
    depth_from_ancestor_to_b: int | None = None
    total_generation_distance: int | None = None
    path_from_ancestor_to_a: str
    path_from_ancestor_to_b: str
    suggested_kinship: str


class RelationshipExplainResponse(BaseModel):
    relationship_path: RelationshipPathData
    ai_explanation: str
    prompt_used: str
    chat_message_id: UUID | None = None
