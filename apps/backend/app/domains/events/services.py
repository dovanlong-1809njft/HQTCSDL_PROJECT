"""Nghiệp vụ phân hệ Sự kiện: lịch tháng, RSVP, thư viện ảnh, nhắc nhở."""

from uuid import UUID
from datetime import datetime,timezone

from fastapi import HTTPException
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.family_access import require_family_access
from app.domains.identity.models import User
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
        end_date=row.get("EndDate"),
        location=row["Location"],
        going_count=int(row["GoingCount"] or 0),
        my_rsvp=row.get("MyRsvp"),
    )


def list_monthly_events_service(
    family_id: UUID, year: int, month: int, actor: User, db: Session,tz_offset: int=0
) -> list[EventResponse]:
    require_family_access(db, actor, family_id)
    rows = repository.list_monthly_events(db, family_id=family_id, year=year, month=month,tz_offset=tz_offset)
    return [_to_event_response(row) for row in rows]


def _accessible_event(event_id: UUID, actor: User, db: Session, *, for_update: bool=False):
    row = repository.get_event(db, event_id=event_id,actor_id=actor.id,for_update=for_update)
    if row is None:
        raise NotFoundError("Sự kiện không tồn tại.")
    require_family_access(db, actor, row["FamilyId"])
    return row


def get_event_service(event_id: UUID, actor: User, db: Session) -> EventResponse:
    return _to_event_response(_accessible_event(event_id, actor, db))


def create_event_service(payload: EventCreateRequest, actor: User, db: Session) -> EventResponse:
    require_family_access(db, actor, payload.family_id, manage=True)
    try:
        event_id = repository.create_event(
            db,
            family_id=payload.family_id,
            title=payload.title.strip(),
            event_date=payload.event_date,
            end_date=payload.end_date,
            location=payload.location,
        )
    except DBAPIError as exc:
        db.rollback()
        raise NotFoundError("Không tạo được sự kiện: gia đình không tồn tại.") from exc
    return get_event_service(event_id, actor, db)


def upsert_rsvp_service(event_id: UUID, payload: RsvpRequest, actor: User, db: Session) -> RsvpResponse:
    event = _accessible_event(event_id, actor, db)
    if not repository.owns_member(db, payload.member_id, actor.id, event["FamilyId"]):
        raise HTTPException(403, "Chỉ được phản hồi tham dự cho hồ sơ của chính bạn trong gia đình này.")
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
    event_id: UUID, payload: GalleryCreateRequest, actor: User, db: Session
) -> GalleryItemResponse:
    _accessible_event(event_id, actor, db)
    row = repository.add_gallery_item(
        db, event_id=event_id, media_url=payload.media_url, uploaded_by=actor.id
    )
    return GalleryItemResponse(
        id=row["Id"],
        event_id=row["EventId"],
        media_url=row["MediaUrl"],
        uploaded_by=row["UploadedBy"],
        created_at=row["CreatedAt"],
    )


def list_gallery_service(
    event_id: UUID, page: PageParams, actor: User, db: Session
) -> list[GalleryItemResponse]:
    _accessible_event(event_id, actor, db)
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
    event_id: UUID, payload: ReminderCreateRequest, actor: User, db: Session
) -> ReminderResponse:
    event=_accessible_event(event_id, actor, db,for_update=True)
    if payload.for_family:
        require_family_access(db,actor,event["FamilyId"],manage=True)
    event_date=event["EventDate"]
    if event_date.tzinfo:
        event_date=event_date.astimezone(timezone.utc).replace(tzinfo=None)
    if payload.reminder_time<=datetime.now(timezone.utc).replace(tzinfo=None) or payload.reminder_time>event_date:
        raise HTTPException(422,"Nhắc lịch phải ở tương lai và không sau thời gian sự kiện.")
    row = repository.create_reminder(
        db, event_id=event_id, reminder_time=payload.reminder_time,user_id=None if payload.for_family else actor.id
    )
    return ReminderResponse(
        id=row["Id"],
        event_id=row["EventId"],
        reminder_time=row["ReminderTime"],
        status=row["Status"],
        user_id=row.get("UserId"),
    )
