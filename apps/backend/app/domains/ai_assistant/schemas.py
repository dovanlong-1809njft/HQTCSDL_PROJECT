from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class EmbeddingTestRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class EmbeddingTestResponse(BaseModel):
    model: str
    dimensions: int
    preview_first_5: list[float]
    embedding_json: str


class CosineTestRequest(BaseModel):
    text_a: str = Field(..., min_length=1, max_length=2000)
    text_b: str = Field(..., min_length=1, max_length=2000)


class CosineTestResponse(BaseModel):
    text_a: str
    text_b: str
    dimensions: int
    cosine_similarity: float | None


class UpsertChunkRequest(BaseModel):
    family_id: UUID
    source_type: Literal["post", "heritage", "member"]
    source_id: UUID
    chunk_index: int = Field(default=0, ge=0)
    chunk_text: str = Field(..., min_length=1, max_length=2000)
    summary_text: str | None = Field(default=None, max_length=1000)


class UpsertChunkResponse(BaseModel):
    chunk_id: UUID
    action_taken: str
    dimensions: int


class ChunkAndIndexRequest(BaseModel):
    family_id: UUID
    source_type: Literal["post", "heritage", "member"]
    source_id: UUID
    title: str | None = Field(default=None, max_length=300)
    content: str = Field(..., min_length=1, max_length=20000)
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
    family_id: UUID | None = None
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


class SemanticSearchRequest(BaseModel):
    family_id: UUID
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)
    min_score: float = Field(default=0.30, ge=-1.0, le=1.0)
    source_type: Literal["post", "heritage", "member"] | None = None
    generate_answer: bool = True
    user_id: UUID | None = None


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


class RelationshipExplainRequest(BaseModel):
    family_id: UUID
    member_a_id: UUID
    member_b_id: UUID
    question: str | None = Field(default=None, max_length=1000)
    user_id: UUID | None = None


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


class SummarizeRequest(BaseModel):
    family_id: UUID
    source_type: Literal["post", "heritage"] | None = None
    source_id: UUID | None = None
    title: str | None = Field(default=None, max_length=300)
    content: str | None = Field(default=None, max_length=20000)
    max_sentences: int = Field(default=3, ge=1, le=10)
    save_to_chunks: bool = True


class SummarizeResponse(BaseModel):
    family_id: UUID
    source_type: str | None = None
    source_id: UUID | None = None
    title: str
    summary: str
    updated_chunks: int = 0
    chat_message_id: UUID | None = None


class RecommendationRequest(BaseModel):
    family_id: UUID
    member_id: UUID | None = None
    topic_query: str | None = Field(default=None, max_length=500)
    top_k: int = Field(default=4, ge=1, le=10)
    min_score: float = Field(default=0.25, ge=-1.0, le=1.0)


class RecommendedMemberItem(BaseModel):
    member_id: UUID
    full_name: str
    birth_date: date | None = None
    location: str | None = None
    branch_name: str | None = None
    latest_position: str | None = None
    latest_company: str | None = None
    latest_institution: str | None = None
    match_reason: str


class RecommendationResponse(BaseModel):
    family_id: UUID
    anchor_member_id: UUID | None = None
    synthesized_query: str
    related_members: list[RecommendedMemberItem]
    related_resources: list[SemanticSearchHit]
    ai_recommendation_note: str | None = None