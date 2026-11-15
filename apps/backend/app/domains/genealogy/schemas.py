# Pydantic request/response DTO cho domain genealogy
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.shared.pagination import PaginatedResponse


# ---------- Directory ----------
class DirectoryMemberResponse(BaseModel):
    id: UUID
    full_name: str
    birth_date: date | None = None
    location: str | None = None
    family_id: UUID
    branch_id: UUID | None = None
    generation: int
    latest_position: str | None = None
    latest_company: str | None = None
    latest_institution: str | None = None
    latest_degree: str | None = None


DirectorySearchResponse = PaginatedResponse[DirectoryMemberResponse]


# ---------- Member ----------
class MemberCreateRequest(BaseModel):
    family_id: UUID
    branch_id: UUID | None = None
    full_name: str = Field(min_length=1, max_length=255)
    gender: Literal["male", "female", "other"]
    birth_date: date | None = None
    death_date: date | None = None
    location: str | None = None
    bio: str | None = None


class MemberUpdateRequest(BaseModel):
    """Cập nhật từng phần: chỉ các trường được gửi lên mới bị sửa
    (dùng model_dump(exclude_unset=True) ở service)."""

    branch_id: UUID | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    gender: Literal["male", "female", "other"] | None = None
    birth_date: date | None = None
    death_date: date | None = None
    location: str | None = None
    bio: str | None = None


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    family_id: UUID
    branch_id: UUID | None = None
    full_name: str
    gender: str
    birth_date: date | None = None
    death_date: date | None = None
    location: str | None = None
    bio: str | None = None
    created_at: datetime


# ---------- Relationships ----------
class AddChildNodeRequest(BaseModel):
    parent_id: UUID
    child_id: UUID
    relation_type: Literal["biological", "adopted"]


class AddMarriageRequest(BaseModel):
    spouse_a_id: UUID
    spouse_b_id: UUID
    marriage_date: date | None = None
    status: str
