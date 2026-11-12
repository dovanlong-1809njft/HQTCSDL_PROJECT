"""Schema Pydantic cho phân hệ Cộng đồng (bài viết, bình luận, cảm xúc, báo cáo)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MediaItem(BaseModel):
    """Một ảnh đính kèm bài viết. Khớp với OPENJSON trong usp_CreatePostWithMedia."""

    url: str = Field(min_length=1, max_length=2048)
    type: str = Field(default="image", max_length=50)


class PostCreateRequest(BaseModel):
    family_id: UUID
    content: str = Field(min_length=1)
    media: list[MediaItem] = Field(default_factory=list, max_length=20)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    post_id: UUID
    family_id: UUID
    author_id: UUID
    author_name: str | None = None
    content: str
    created_at: datetime
    comment_count: int = 0
    reaction_count: int = 0
    media_urls: list[str] = Field(default_factory=list)


class CommentCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    id: UUID
    post_id: UUID
    user_id: UUID
    author_name: str | None = None
    content: str
    created_at: datetime


class ReactionRequest(BaseModel):
    """type = None nghĩa là gỡ cảm xúc (usp_UpsertReaction xử lý)."""

    type: str | None = Field(default=None, max_length=20)


class ReactionResponse(BaseModel):
    post_id: UUID
    user_id: UUID
    type: str | None = None
    reaction_count: int = 0


class ReportCreateRequest(BaseModel):
    target_id: UUID
    target_type: str = Field(pattern="^(post|comment|photo)$")
    reason: str = Field(min_length=1, max_length=500)


class ReportResponse(BaseModel):
    id: UUID
    target_id: UUID
    target_type: str
    status: str
    created_at: datetime
