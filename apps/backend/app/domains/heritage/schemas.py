"""TV4 contracts: client-supplied actor and owner fields are rejected."""
from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Version = Annotated[str, StringConstraints(pattern=r"^[A-Fa-f0-9]{64}$")]
ItemType = Literal["document", "story", "photo"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, str_strip_whitespace=True)


class ItemFields(Contract):
    type: ItemType
    title: Title
    description: str | None = Field(default=None, max_length=500)
    content: str | None = Field(default=None, max_length=200000)
    media_url: str | None = Field(default=None, max_length=500)

    @field_validator("description", "content", "media_url")
    @classmethod
    def blank_to_none(cls, value):
        return value or None

    @field_validator("media_url")
    @classmethod
    def safe_url(cls, value):
        if value is None:
            return None
        if any(c.isspace() or ord(c) < 32 for c in value) or "\\" in value:
            raise ValueError("URL media không hợp lệ.")
        parsed = urlsplit(value)
        local = value.startswith("/") and not value.startswith("//")
        remote = parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password
        if not (local or remote):
            raise ValueError("Dùng URL HTTPS hoặc đường dẫn /media/ có sẵn.")
        return value

    @model_validator(mode="after")
    def validate_payload(self):
        if self.type == "photo" and not self.media_url:
            raise ValueError("Ảnh cần URL media.")
        if self.type == "story" and not self.content:
            raise ValueError("Câu chuyện cần nội dung.")
        if self.type == "document" and not (self.content or self.media_url):
            raise ValueError("Tài liệu cần nội dung hoặc URL.")
        return self


class ItemCreate(ItemFields):
    pass


class ItemPatch(Contract):
    expected_version: Version
    type: ItemType | None = None
    title: Title | None = None
    description: str | None = Field(default=None, max_length=500)
    content: str | None = Field(default=None, max_length=200000)
    media_url: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def required_non_null(self):
        if any(name in self.model_fields_set and getattr(self, name) is None for name in ("type", "title")):
            raise ValueError("Loại và tiêu đề không được null.")
        return self


class ItemResponse(Contract):
    id: UUID = Field(validation_alias="Id")
    family_id: UUID = Field(validation_alias="FamilyId")
    created_by_user_id: UUID = Field(validation_alias="CreatedByUserId")
    type: ItemType = Field(validation_alias="Type")
    title: str = Field(validation_alias="Title")
    description: str | None = Field(validation_alias="Description")
    content: str | None = Field(validation_alias="Content")
    media_url: str | None = Field(validation_alias="MediaUrl")
    created_at: datetime = Field(validation_alias="CreatedAt")
    version_token: str = Field(validation_alias="VersionToken")


class HonorFields(Contract):
    title: Title
    description: str | None = Field(default=None, max_length=1000)
    date_awarded: date | None = None


class HonorCreate(HonorFields):
    member_id: UUID


class HonorPatch(Contract):
    expected_version: Version
    title: Title | None = None
    description: str | None = Field(default=None, max_length=1000)
    date_awarded: date | None = None

    @model_validator(mode="after")
    def required_non_null(self):
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("Tiêu đề không được null.")
        return self


class HonorResponse(Contract):
    id: UUID = Field(validation_alias="Id")
    member_id: UUID = Field(validation_alias="MemberId")
    family_id: UUID = Field(validation_alias="FamilyId")
    full_name: str = Field(validation_alias="FullName")
    title: str = Field(validation_alias="Title")
    description: str | None = Field(validation_alias="Description")
    date_awarded: date | None = Field(validation_alias="DateAwarded")
    created_at: datetime = Field(validation_alias="CreatedAt")
    version_token: str = Field(validation_alias="VersionToken")


class FamilyResponse(Contract):
    id: UUID = Field(validation_alias="Id")
    name: str = Field(validation_alias="Name")


class MemberResponse(Contract):
    id: UUID = Field(validation_alias="Id")
    full_name: str = Field(validation_alias="FullName")


class RankingResponse(Contract):
    family_id: UUID = Field(validation_alias="FamilyId")
    member_id: UUID = Field(validation_alias="MemberId")
    full_name: str = Field(validation_alias="FullName")
    honor_count: int = Field(validation_alias="HonorCount")
    rank: int = Field(validation_alias="Rank")


class TreeNode(Contract):
    id: UUID
    label: str
    birth_date: date | None = None


class TreeEdge(Contract):
    id: str
    source: UUID
    target: UUID
    kind: Literal["parent_child", "marriage"]


class FamilyTree(Contract):
    family_id: UUID
    nodes: list[TreeNode]
    edges: list[TreeEdge]
