"""Schema Pydantic cho phân hệ Sự kiện (lịch, RSVP, thư viện ảnh, nhắc nhở)."""

from datetime import datetime,timezone
from uuid import UUID

from pydantic import BaseModel,ConfigDict, Field, HttpUrl, TypeAdapter,field_validator


class EventCreateRequest(BaseModel):
    model_config=ConfigDict(extra="forbid",str_strip_whitespace=True)
    family_id: UUID
    title: str = Field(min_length=1, max_length=200)
    event_date: datetime
    location: str | None = Field(default=None, max_length=500)

    @field_validator("event_date")
    @classmethod
    def utc_date(cls,value):
        value=value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value
        if not 1900<=value.year<=2200:
            raise ValueError("Thời gian sự kiện cần nằm trong năm 1900–2200.")
        return value


class EventUpdateRequest(EventCreateRequest):
    family_id: None=None


class EventResponse(BaseModel):
    event_id: UUID
    family_id: UUID
    title: str
    event_date: datetime
    location: str | None = None
    going_count: int = 0
    my_rsvp: str | None=None


class RsvpRequest(BaseModel):
    member_id: UUID
    rsvp_status: str = Field(pattern="^(Pending|Going|Maybe|Declined)$")


class RsvpResponse(BaseModel):
    event_id: UUID
    member_id: UUID
    rsvp_status: str
    going_count: int = 0


class GalleryCreateRequest(BaseModel):
    media_url: str = Field(min_length=1, max_length=2048)

    @field_validator("media_url")
    @classmethod
    def http_url(cls,value):
        value=value.strip()
        TypeAdapter(HttpUrl).validate_python(value)
        return value


class GalleryItemResponse(BaseModel):
    id: UUID
    event_id: UUID
    media_url: str
    uploaded_by: UUID
    created_at: datetime


class ReminderCreateRequest(BaseModel):
    reminder_time: datetime
    for_family: bool=False

    @field_validator("reminder_time")
    @classmethod
    def utc_date(cls,value):
        return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value


class ReminderResponse(BaseModel):
    id: UUID
    event_id: UUID
    reminder_time: datetime
    status: str
    user_id: UUID | None=None
