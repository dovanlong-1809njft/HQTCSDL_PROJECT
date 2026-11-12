"""API phân hệ Sự kiện: lịch tháng, RSVP, thư viện ảnh và nhắc nhở."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.domains.events.schemas import (
    EventCreateRequest,
    EventResponse,
    GalleryCreateRequest,
    GalleryItemResponse,
    ReminderCreateRequest,
    ReminderResponse,
    RsvpRequest,
    RsvpResponse,
)
from app.domains.events.services import (
    add_gallery_item_service,
    create_event_service,
    create_reminder_service,
    get_event_service,
    list_gallery_service,
    list_monthly_events_service,
    upsert_rsvp_service,
)
from app.domains.identity.models import User
from app.shared.pagination import PageParams

router = APIRouter(prefix="/events", tags=["events"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[EventResponse])
def list_monthly_events(
    family_id: UUID,
    year: Annotated[int, Query(ge=1900, le=2200)],
    month: Annotated[int, Query(ge=1, le=12)],
    current_user: CurrentUser,
    db: DbSession,
) -> list[EventResponse]:
    """Lịch sự kiện theo tháng, đọc qua Function fn_GetMonthlyEvents."""
    return list_monthly_events_service(family_id, year, month, db)


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreateRequest, current_user: CurrentUser, db: DbSession) -> EventResponse:
    return create_event_service(payload, db)


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: UUID, current_user: CurrentUser, db: DbSession) -> EventResponse:
    return get_event_service(event_id, db)


@router.put("/{event_id}/rsvp", response_model=RsvpResponse)
def upsert_rsvp(
    event_id: UUID, payload: RsvpRequest, current_user: CurrentUser, db: DbSession
) -> RsvpResponse:
    """Trả lời tham dự. Gọi lại nhiều lần chỉ cập nhật, không tạo dòng trùng (MERGE)."""
    return upsert_rsvp_service(event_id, payload, db)


@router.post(
    "/{event_id}/gallery",
    response_model=GalleryItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_gallery_item(
    event_id: UUID, payload: GalleryCreateRequest, current_user: CurrentUser, db: DbSession
) -> GalleryItemResponse:
    return add_gallery_item_service(event_id, payload, current_user.id, db)


@router.get("/{event_id}/gallery", response_model=list[GalleryItemResponse])
def list_gallery(
    event_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 30,
) -> list[GalleryItemResponse]:
    """Thư viện ảnh của sự kiện."""
    return list_gallery_service(event_id, PageParams(page=page, page_size=page_size), db)


@router.post(
    "/{event_id}/reminders",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reminder(
    event_id: UUID, payload: ReminderCreateRequest, current_user: CurrentUser, db: DbSession
) -> ReminderResponse:
    """Đặt nhắc nhở. Worker nền sẽ lấy và gửi khi tới giờ (usp_ClaimDueReminders)."""
    return create_reminder_service(event_id, payload, db)
