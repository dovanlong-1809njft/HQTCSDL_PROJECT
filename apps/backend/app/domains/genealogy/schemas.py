from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NameFields(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=200)


class MemberFields(NameFields):
    branch_id: UUID | None = None
    birth_date: date | None = None
    location: str | None = Field(default=None, max_length=300)

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
