"""Truy vấn CSDL cho domain events.

Lịch tháng đọc qua Function community.fn_GetMonthlyEvents, RSVP ghi qua
Stored Procedure community.usp_UpsertEventRsvp.
"""

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def list_monthly_events(
    db: Session, *, family_id: UUID, year: int, month: int
) -> list[Mapping[str, Any]]:
    """Gọi Function community.fn_GetMonthlyEvents để dựng lịch tháng."""
    stmt = text(
        """
        SELECT EventId, FamilyId, Title, EventDate, Location, GoingCount
        FROM community.fn_GetMonthlyEvents(:family_id, :year, :month)
        ORDER BY EventDate
        """
    )
    return list(
        db.execute(stmt, {"family_id": str(family_id), "year": year, "month": month})
        .mappings()
        .all()
    )


def get_event(db: Session, *, event_id: UUID) -> Mapping[str, Any] | None:
    stmt = text(
        """
        SELECT e.Id AS EventId, e.FamilyId, e.Title, e.EventDate, e.Location,
               (SELECT COUNT_BIG(*) FROM community.EventParticipants AS ep
                WHERE ep.EventId = e.Id AND ep.RsvpStatus = N'Going') AS GoingCount
        FROM community.Events AS e
        WHERE e.Id = :event_id
        """
    )
    return db.execute(stmt, {"event_id": str(event_id)}).mappings().one_or_none()


def create_event(
    db: Session,
    *,
    family_id: UUID,
    title: str,
    event_date: datetime,
    location: str | None,
) -> UUID:
    stmt = text(
        """
        INSERT INTO community.Events (FamilyId, Title, EventDate, Location)
        OUTPUT inserted.Id
        VALUES (:family_id, :title, :event_date, :location)
        """
    )
    event_id = db.execute(
        stmt,
        {
            "family_id": str(family_id),
            "title": title,
            "event_date": event_date,
            "location": location,
        },
    ).scalar_one()
    db.commit()
    return UUID(str(event_id))


def upsert_rsvp(db: Session, *, event_id: UUID, member_id: UUID, rsvp_status: str) -> None:
    """Gọi community.usp_UpsertEventRsvp (MERGE): chưa trả lời thì thêm, đã có thì cập nhật."""
    stmt = text(
        """
        EXEC community.usp_UpsertEventRsvp
            @EventId    = :event_id,
            @MemberId   = :member_id,
            @RsvpStatus = :rsvp_status
        """
    )
    db.execute(
        stmt,
        {"event_id": str(event_id), "member_id": str(member_id), "rsvp_status": rsvp_status},
    )
    db.commit()


def add_gallery_item(
    db: Session, *, event_id: UUID, media_url: str, uploaded_by: UUID
) -> Mapping[str, Any]:
    stmt = text(
        """
        INSERT INTO community.EventGalleries (EventId, MediaUrl, UploadedBy)
        OUTPUT inserted.Id, inserted.EventId, inserted.MediaUrl, inserted.UploadedBy, inserted.CreatedAt
        VALUES (:event_id, :media_url, :uploaded_by)
        """
    )
    row = (
        db.execute(
            stmt,
            {"event_id": str(event_id), "media_url": media_url, "uploaded_by": str(uploaded_by)},
        )
        .mappings()
        .one()
    )
    db.commit()
    return row


def list_gallery(db: Session, *, event_id: UUID, offset: int, limit: int) -> list[Mapping[str, Any]]:
    stmt = text(
        """
        SELECT Id, EventId, MediaUrl, UploadedBy, CreatedAt
        FROM community.EventGalleries
        WHERE EventId = :event_id
        ORDER BY CreatedAt DESC
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """
    )
    return list(
        db.execute(stmt, {"event_id": str(event_id), "offset": offset, "limit": limit})
        .mappings()
        .all()
    )


def create_reminder(db: Session, *, event_id: UUID, reminder_time: datetime) -> Mapping[str, Any]:
    stmt = text(
        """
        INSERT INTO community.EventReminders (EventId, ReminderTime)
        OUTPUT inserted.Id, inserted.EventId, inserted.ReminderTime, inserted.Status
        VALUES (:event_id, :reminder_time)
        """
    )
    row = (
        db.execute(stmt, {"event_id": str(event_id), "reminder_time": reminder_time})
        .mappings()
        .one()
    )
    db.commit()
    return row


def claim_due_reminders(db: Session, *, batch_size: int = 50) -> list[Mapping[str, Any]]:
    """Gọi community.usp_ClaimDueReminders.

    SP dùng UPDLOCK + READPAST nên nhiều worker chạy song song không lấy trùng
    một nhắc nhở và không phải chờ nhau.
    """
    stmt = text("EXEC community.usp_ClaimDueReminders @BatchSize = :batch_size")
    rows = list(db.execute(stmt, {"batch_size": batch_size}).mappings().all())
    db.commit()
    return rows


def mark_reminder_failed(db: Session, *, reminder_id: UUID) -> None:
    """Worker gọi khi gửi thông báo lỗi, trả nhắc nhở về trạng thái failed."""
    stmt = text(
        "UPDATE community.EventReminders SET Status = N'failed' WHERE Id = :reminder_id"
    )
    db.execute(stmt, {"reminder_id": str(reminder_id)})
    db.commit()
