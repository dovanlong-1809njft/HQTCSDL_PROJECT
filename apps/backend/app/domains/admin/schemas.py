from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StrictBool, StringConstraints, field_validator


ConfigKey = Annotated[str, StringConstraints(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")]
ReportStatus = Literal["pending", "resolved", "dismissed"]


class SiteSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    site_name: str = Field(min_length=1, max_length=60)
    logo_url: str = Field(min_length=1, max_length=2048)
    theme: Literal["forest", "ocean", "warm"]
    registration_enabled: StrictBool

    @field_validator("logo_url")
    @classmethod
    def safe_logo(cls, value):
        if any(character.isspace() or ord(character) < 32 or character == "\\" for character in value):
            raise ValueError("URL logo không hợp lệ.")
        parsed = urlsplit(value)
        local = value.startswith("/") and not value.startswith("//")
        remote = parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password
        if not (local or remote):
            raise ValueError("Logo cần URL HTTPS hoặc đường dẫn bắt đầu bằng /.")
        return value

    @field_validator("registration_enabled", mode="before")
    @classmethod
    def stored_boolean(cls, value):
        if isinstance(value, str) and value.lower() in ("true", "false"):
            return value.lower() == "true"
        return value


DEFAULT_SITE_SETTINGS = SiteSettings(site_name="FamilyConnect", logo_url="/favicon.svg", theme="forest", registration_enabled=True)
SITE_CONFIG_KEYS = {
    "site.name": ("site_name", "Tên hiển thị của website"),
    "site.logo_url": ("logo_url", "Đường dẫn logo website"),
    "site.theme": ("theme", "Màu giao diện website"),
    "registration.enabled": ("registration_enabled", "Cho phép đăng ký tài khoản mới"),
}


class AdminSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class BackupResponse(AdminSchema):
    id: UUID
    file_name: str
    created_at: datetime
    size_bytes: int


class BackupsResponse(AdminSchema):
    database: str
    backups: list[BackupResponse]


class RestoreRequest(AdminSchema):
    database: str = Field(min_length=1, max_length=128)
    password: SecretStr = Field(min_length=1, max_length=128)


class RestoreResponse(AdminSchema):
    database: str
    safety_backup_id: UUID
    message: str


class SystemConfigCreate(AdminSchema):
    config_key: ConfigKey
    config_value: str = Field(min_length=1, pattern=r"\S")
    description: str = Field(min_length=1, max_length=500, pattern=r"\S")


class SystemConfigUpdate(AdminSchema):
    config_value: str = Field(min_length=1, pattern=r"\S")
    description: str = Field(min_length=1, max_length=500, pattern=r"\S")


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


class FamilyActivityResponse(AdminSchema):
    family_id: UUID = Field(validation_alias="FamilyId")
    family_name: str = Field(validation_alias="FamilyName")
    member_count: int = Field(validation_alias="MemberCount", ge=0)
    post_count: int = Field(validation_alias="PostCount", ge=0)
    event_count: int = Field(validation_alias="EventCount", ge=0)


class ReportedContentResponse(AdminSchema):
    report_id: UUID = Field(validation_alias="ReportId")
    target_id: UUID = Field(validation_alias="TargetId")
    target_type: Literal["post", "comment", "photo"] = Field(validation_alias="TargetType")
    reporter_name: str = Field(validation_alias="ReporterName")
    reason: str = Field(validation_alias="Reason")
    status: ReportStatus = Field(validation_alias="Status")
    created_at: datetime = Field(validation_alias="CreatedAt")
    family_name: str | None = Field(validation_alias="FamilyName")
    target_content: str | None = Field(validation_alias="TargetContent")
    can_resolve: bool = Field(validation_alias="CanResolve")


class ResolveReportRequest(AdminSchema):
    decision: Literal["resolved", "dismissed"]


class ResolveReportResponse(AdminSchema):
    report_id: UUID = Field(validation_alias="ReportId")
    status: Literal["resolved", "dismissed"] = Field(validation_alias="Status")
    deleted_target_count: int = Field(validation_alias="DeletedTargetCount", ge=0)
    resolved_report_count: int = Field(validation_alias="ResolvedReportCount", ge=0)
