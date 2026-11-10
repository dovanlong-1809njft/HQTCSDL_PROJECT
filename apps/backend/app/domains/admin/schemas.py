from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


ConfigKey = Annotated[str, StringConstraints(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")]


class AdminSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SystemConfigCreate(AdminSchema):
    config_key: ConfigKey
    config_value: str
    description: str | None = Field(default=None, max_length=500)


class SystemConfigUpdate(AdminSchema):
    config_value: str
    description: str | None = Field(default=None, max_length=500)


class SystemConfigResponse(AdminSchema):
    config_key: str = Field(validation_alias="ConfigKey")
    config_value: str = Field(validation_alias="ConfigValue")
    description: str | None = Field(validation_alias="Description")
    updated_at: datetime = Field(validation_alias="UpdatedAt")


class PendingVerificationResponse(AdminSchema):
    verification_id: UUID = Field(validation_alias="VerificationId")
    user_id: UUID = Field(validation_alias="UserId")
    user_full_name: str = Field(validation_alias="UserFullName")
    user_email: str = Field(validation_alias="UserEmail")
    user_is_active: bool = Field(validation_alias="UserIsActive")
    member_id: UUID = Field(validation_alias="MemberId")
    member_full_name: str = Field(validation_alias="MemberFullName")
    birth_date: date | None = Field(validation_alias="BirthDate")
    family_id: UUID = Field(validation_alias="FamilyId")
    family_name: str = Field(validation_alias="FamilyName")
    branch_id: UUID | None = Field(validation_alias="BranchId")
    branch_name: str | None = Field(validation_alias="BranchName")
    linked_user_id: UUID | None = Field(validation_alias="LinkedUserId")
    status: Literal["pending"] = Field(validation_alias="Status")
    requested_at: datetime = Field(validation_alias="RequestedAt")


class ReviewVerificationRequest(AdminSchema):
    decision: Literal["approved", "rejected"]


class ReviewVerificationResponse(AdminSchema):
    verification_id: UUID = Field(validation_alias="VerificationId")
    status: Literal["approved", "rejected"] = Field(validation_alias="Status")
    auto_rejected_count: int = Field(validation_alias="AutoRejectedCount", ge=0)
