from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.shared.pagination import PaginatedResponse


class NameFields(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=200)


class MemberFields(NameFields):
    branch_id: UUID | None = None
    birth_date: date | None = None
    location: str | None = Field(default=None, min_length=1, max_length=300)

    @field_validator("birth_date")
    @classmethod
    def past_birth_date(cls, value):
        if value and value > date.today():
            raise ValueError("Ngày sinh không được ở tương lai.")
        return value


class ProfileFields(MemberFields):
    branch_id: None = None


class VerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    member_id: UUID


class RelationshipFields(BaseModel):
    model_config = ConfigDict(extra="forbid")
    first_id: UUID
    second_id: UUID
    married_date: date | None = None


# ---------- Directory (TV2) ----------
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


class MemberCreateRequest(BaseModel):
    family_id: UUID
    branch_id: UUID | None = None
    full_name: str = Field(min_length=1, max_length=255)
    gender: Literal["male", "female", "other"] | None = None
    birth_date: date | None = None
    death_date: date | None = None
    location: str | None = None
    bio: str | None = None


class MemberUpdateRequest(BaseModel):
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
    gender: str | None = None
    birth_date: date | None = None
    death_date: date | None = None
    location: str | None = None
    bio: str | None = None
    created_at: datetime | None = None


class AddChildNodeRequest(BaseModel):
    parent_id: UUID
    child_id: UUID
    relation_type: Literal["biological", "adopted"] = "biological"


class AddMarriageRequest(BaseModel):
    spouse_a_id: UUID
    spouse_b_id: UUID
    marriage_date: date | None = None
    status: str | None = None
