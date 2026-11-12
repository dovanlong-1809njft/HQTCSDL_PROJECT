"""Schema Pydantic cho phân hệ Sự kiện (lịch, RSVP, thư viện ảnh, nhắc nhở)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EventCreateRequest(BaseModel):
    family_id: UUID
    title: str = Field(min_length=1, max_length=200)
    event_date: datetime
    location: str | None = Field(default=None, max_length=500)


class EventResponse(BaseModel):
    event_id: UUID
    family_id: UUID
    title: str
    event_date: datetime
    location: str | None = None
    going_count: int = 0


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


class GalleryItemResponse(BaseModel):
    id: UUID
    event_id: UUID
    media_url: str
    uploaded_by: UUID
    created_at: datetime


class ReminderCreateRequest(BaseModel):
    reminder_time: datetime


class ReminderResponse(BaseModel):
    id: UUID
    event_id: UUID
    reminder_time: datetime
    status: str
