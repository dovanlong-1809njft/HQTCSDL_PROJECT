from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


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
    family_id: UUID
    source_type: Literal["post", "heritage", "member"] = "heritage"
    source_id: UUID
    chunk_index: int = Field(default=0, ge=0)
    chunk_text: str = Field(min_length=1, max_length=2000)
    summary_text: str | None = Field(default=None, max_length=1000)


class UpsertChunkResponse(BaseModel):
    chunk_id: UUID
    action_taken: str
    dimensions: int
