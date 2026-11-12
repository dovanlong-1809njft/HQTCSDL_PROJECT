"""Nghiệp vụ phân hệ Sự kiện: lịch tháng, RSVP, thư viện ảnh, nhắc nhở."""

from uuid import UUID

from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domains.events import repository
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
from app.shared.pagination import PageParams


def _to_event_response(row) -> EventResponse:
    return EventResponse(
        event_id=row["EventId"],
        family_id=row["FamilyId"],
        title=row["Title"],
        event_date=row["EventDate"],
        location=row["Location"],
        going_count=int(row["GoingCount"] or 0),
    )


def list_monthly_events_service(
    family_id: UUID, year: int, month: int, db: Session
) -> list[EventResponse]:
    rows = repository.list_monthly_events(db, family_id=family_id, year=year, month=month)
    return [_to_event_response(row) for row in rows]


def get_event_service(event_id: UUID, db: Session) -> EventResponse:
    row = repository.get_event(db, event_id=event_id)
    if row is None:
        raise NotFoundError("Sự kiện không tồn tại.")
    return _to_event_response(row)


def create_event_service(payload: EventCreateRequest, db: Session) -> EventResponse:
    try:
        event_id = repository.create_event(
            db,
            family_id=payload.family_id,
            title=payload.title.strip(),
            event_date=payload.event_date,
            location=payload.location,
        )
    except DBAPIError as exc:
        db.rollback()
        raise NotFoundError("Không tạo được sự kiện: gia đình không tồn tại.") from exc
    return get_event_service(event_id, db)


def upsert_rsvp_service(event_id: UUID, payload: RsvpRequest, db: Session) -> RsvpResponse:
    try:
        repository.upsert_rsvp(
            db,
            event_id=event_id,
            member_id=payload.member_id,
            rsvp_status=payload.rsvp_status,
        )
    except DBAPIError as exc:  # THROW 50721 khi sự kiện không tồn tại
        db.rollback()
        raise NotFoundError("Không ghi được RSVP: sự kiện hoặc thành viên không hợp lệ.") from exc

    event = repository.get_event(db, event_id=event_id)
    return RsvpResponse(
        event_id=event_id,
        member_id=payload.member_id,
        rsvp_status=payload.rsvp_status,
        going_count=int(event["GoingCount"] or 0) if event else 0,
    )


def add_gallery_item_service(
    event_id: UUID, payload: GalleryCreateRequest, user_id: UUID, db: Session
) -> GalleryItemResponse:
    if repository.get_event(db, event_id=event_id) is None:
        raise NotFoundError("Sự kiện không tồn tại.")
    row = repository.add_gallery_item(
        db, event_id=event_id, media_url=payload.media_url, uploaded_by=user_id
    )
    return GalleryItemResponse(
        id=row["Id"],
        event_id=row["EventId"],
        media_url=row["MediaUrl"],
        uploaded_by=row["UploadedBy"],
        created_at=row["CreatedAt"],
    )


def list_gallery_service(
    event_id: UUID, page: PageParams, db: Session
) -> list[GalleryItemResponse]:
    rows = repository.list_gallery(db, event_id=event_id, offset=page.offset, limit=page.page_size)
    return [
        GalleryItemResponse(
            id=row["Id"],
            event_id=row["EventId"],
            media_url=row["MediaUrl"],
            uploaded_by=row["UploadedBy"],
            created_at=row["CreatedAt"],
        )
        for row in rows
    ]


def create_reminder_service(
    event_id: UUID, payload: ReminderCreateRequest, db: Session
) -> ReminderResponse:
    if repository.get_event(db, event_id=event_id) is None:
        raise NotFoundError("Sự kiện không tồn tại.")
    row = repository.create_reminder(
        db, event_id=event_id, reminder_time=payload.reminder_time
    )
    return ReminderResponse(
        id=row["Id"],
        event_id=row["EventId"],
        reminder_time=row["ReminderTime"],
        status=row["Status"],
    )
