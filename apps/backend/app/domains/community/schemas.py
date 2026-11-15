"""Schema Pydantic cho phân hệ Cộng đồng (bài viết, bình luận, cảm xúc, báo cáo)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, TypeAdapter, field_validator


class MediaItem(BaseModel):
    """Một ảnh đính kèm bài viết. Khớp với OPENJSON trong usp_CreatePostWithMedia."""

    url: str = Field(min_length=1, max_length=2048)
    type: str = Field(default="image", max_length=50)

    @field_validator("url")
    @classmethod
    def http_url(cls,value):
        value=value.strip()
        TypeAdapter(HttpUrl).validate_python(value)
        return value


class PostCreateRequest(BaseModel):
    model_config=ConfigDict(extra="forbid",str_strip_whitespace=True)
    family_id: UUID
    content: str = Field(min_length=1,max_length=20000)
    media: list[MediaItem] = Field(default_factory=list, max_length=20)
    is_announcement: bool=False


class PostUpdateRequest(PostCreateRequest):
    family_id: None=None


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
    is_announcement: bool=False
    my_reaction: str | None=None


class CommentCreateRequest(BaseModel):
    model_config=ConfigDict(extra="forbid",str_strip_whitespace=True)
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

    type: str | None = Field(default=None, pattern="^(Like|Love|Haha|Wow|Sad|Angry)$")


class ReactionResponse(BaseModel):
    post_id: UUID
    user_id: UUID
    type: str | None = None
    reaction_count: int = 0


class ReportCreateRequest(BaseModel):
    model_config=ConfigDict(extra="forbid",str_strip_whitespace=True)
    target_id: UUID
    target_type: str = Field(pattern="^(post|comment|photo)$")
    reason: str = Field(min_length=1, max_length=500)


class ReportResponse(BaseModel):
    id: UUID
    target_id: UUID
    target_type: str
    status: str
    created_at: datetime
