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
    db: Session, *, family_id: UUID, year: int, month: int,tz_offset: int=0
) -> list[Mapping[str, Any]]:
    """Gọi Function community.fn_GetMonthlyEvents để dựng lịch tháng."""
    if tz_offset:
        stmt=text("""SELECT e.Id AS EventId,e.FamilyId,e.Title,e.EventDate,e.Location,
            (SELECT COUNT(*) FROM community.EventParticipants p WHERE p.EventId=e.Id AND p.RsvpStatus='Going') AS GoingCount
            FROM community.Events e WHERE FamilyId=:family_id
            AND EventDate>=DATEADD(MINUTE,-:tz_offset,CAST(DATEFROMPARTS(:year,:month,1) AS DATETIME2))
            AND EventDate<DATEADD(MINUTE,-:tz_offset,DATEADD(MONTH,1,CAST(DATEFROMPARTS(:year,:month,1) AS DATETIME2)))
            ORDER BY EventDate,e.Id""")
        return list(db.execute(stmt,dict(family_id=str(family_id),year=year,month=month,tz_offset=tz_offset)).mappings().all())
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


def get_event(db: Session, *, event_id: UUID,actor_id: UUID | None=None,for_update: bool=False) -> Mapping[str, Any] | None:
    stmt = text(
        f"""
        SELECT e.Id AS EventId, e.FamilyId, e.Title, e.EventDate, e.Location,
               (SELECT COUNT_BIG(*) FROM community.EventParticipants AS ep
                WHERE ep.EventId = e.Id AND ep.RsvpStatus = N'Going') AS GoingCount,
               (SELECT ep.RsvpStatus FROM community.EventParticipants ep JOIN genealogy.Members m ON m.Id=ep.MemberId
                WHERE ep.EventId=e.Id AND m.UserId=:actor_id) AS MyRsvp
        FROM community.Events AS e {"WITH(UPDLOCK,HOLDLOCK)" if for_update else ""}
        WHERE e.Id = :event_id
        """
    )
    return db.execute(stmt, {"event_id": str(event_id),"actor_id":str(actor_id) if actor_id else None}).mappings().one_or_none()


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


def owns_member(db: Session, member_id: UUID, actor_id: UUID, family_id: UUID) -> bool:
    return db.execute(text("""
        SELECT 1 FROM genealogy.Members
        WHERE Id=:member_id AND UserId=:actor_id AND FamilyId=:family_id
    """), {"member_id": str(member_id), "actor_id": str(actor_id), "family_id": str(family_id)}).scalar_one_or_none() is not None


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


def create_reminder(db: Session, *, event_id: UUID, reminder_time: datetime,user_id: UUID | None=None) -> Mapping[str, Any]:
    stmt = text(
        """
        INSERT INTO community.EventReminders (EventId, ReminderTime,UserId)
        OUTPUT inserted.Id, inserted.EventId, inserted.ReminderTime, inserted.Status,inserted.UserId
        VALUES (:event_id, :reminder_time,:user_id)
        """
    )
    row = (
        db.execute(stmt, {"event_id": str(event_id), "reminder_time": reminder_time,"user_id":str(user_id) if user_id else None})
        .mappings()
        .one()
    )
    db.commit()
    return row
