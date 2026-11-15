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
from app.domains.events.schemas import EventUpdateRequest
from app.domains.genealogy.repository import rows
from app.domains.genealogy.services import run
from app.domains.heritage.repository import execute
from app.domains.events.services import _accessible_event

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
    tz_offset: int=Query(default=0,ge=-840,le=840),
) -> list[EventResponse]:
    """Lịch sự kiện theo tháng, đọc qua Function fn_GetMonthlyEvents."""
    return list_monthly_events_service(family_id, year, month, current_user, db,tz_offset)


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreateRequest, current_user: CurrentUser, db: DbSession) -> EventResponse:
    return create_event_service(payload, current_user, db)


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: UUID, current_user: CurrentUser, db: DbSession) -> EventResponse:
    return get_event_service(event_id, current_user, db)


@router.put("/{event_id}",response_model=EventResponse)
def update_event(event_id: UUID,payload: EventUpdateRequest,current_user: CurrentUser,db: DbSession):
    def operation():
        execute(db,"""EXEC community.usp_ManageEvent @ActorUserId=:actor,@EventId=:id,@Action='update',
            @Title=:title,@EventDate=:event_date,@Location=:location""",dict(actor=current_user.id,id=event_id,**payload.model_dump(exclude={"family_id"}))).close()
        return get_event_service(event_id,current_user,db)
    return run(db,operation,write=True)


@router.delete("/{event_id}",status_code=204)
def delete_event(event_id: UUID,current_user: CurrentUser,db: DbSession):
    run(db,lambda: execute(db,"EXEC community.usp_ManageEvent @ActorUserId=:actor,@EventId=:id,@Action='delete'",dict(actor=current_user.id,id=event_id)).close(),write=True)


@router.get("/{event_id}/participants")
def participants(event_id: UUID,current_user: CurrentUser,db: DbSession,page: int=Query(default=1,ge=1),page_size: int=Query(default=30,ge=1,le=100)):
    def operation():
        _accessible_event(event_id,current_user,db)
        items=rows(db,"""SELECT ep.MemberId AS member_id,m.FullName AS name,ep.RsvpStatus AS rsvp_status,b.Name AS branch_name
            FROM community.EventParticipants ep JOIN genealogy.Members m ON m.Id=ep.MemberId LEFT JOIN core.Branches b ON b.Id=m.BranchId
            WHERE ep.EventId=:id ORDER BY m.FullName,m.Id OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY""",id=event_id,offset=(page-1)*page_size,limit=page_size)
        counts=rows(db,"SELECT RsvpStatus AS status,COUNT(*) AS total FROM community.EventParticipants WHERE EventId=:id GROUP BY RsvpStatus",id=event_id)
        return dict(items=items,total=sum(row["total"] for row in counts),counts={row["status"]:row["total"] for row in counts})
    return run(db,operation)


@router.put("/{event_id}/participants/{member_id}",status_code=204)
def manage_participant(event_id: UUID,member_id: UUID,payload: RsvpRequest,current_user: CurrentUser,db: DbSession):
    if member_id!=payload.member_id:
        from fastapi import HTTPException
        raise HTTPException(422,"Mã thành viên không khớp.")
    run(db,lambda: execute(db,"EXEC community.usp_ManageEvent @ActorUserId=:actor,@EventId=:id,@Action='participant',@MemberId=:member,@RsvpStatus=:status",dict(actor=current_user.id,id=event_id,member=member_id,status=payload.rsvp_status)).close(),write=True)


@router.delete("/{event_id}/gallery/{identifier}",status_code=204)
def remove_gallery(event_id: UUID,identifier: UUID,current_user: CurrentUser,db: DbSession):
    run(db,lambda: execute(db,"EXEC community.usp_ManageEvent @ActorUserId=:actor,@EventId=:id,@Action='gallery-delete',@GalleryId=:gallery",dict(actor=current_user.id,id=event_id,gallery=identifier)).close(),write=True)


@router.get("/{event_id}/reminders",response_model=list[ReminderResponse])
def reminders(event_id: UUID,current_user: CurrentUser,db: DbSession):
    def operation():
        _accessible_event(event_id,current_user,db)
        return rows(db,"""SELECT Id AS id,EventId AS event_id,ReminderTime AS reminder_time,Status AS status,UserId AS user_id
            FROM community.EventReminders WHERE EventId=:id AND (UserId=:actor OR UserId IS NULL OR :manager=1)
            ORDER BY ReminderTime,Id""",id=event_id,actor=current_user.id,manager=current_user.role in ('admin','family_head'))
    return run(db,operation)


@router.delete("/{event_id}/reminders/{identifier}",status_code=204)
def cancel_reminder(event_id: UUID,identifier: UUID,current_user: CurrentUser,db: DbSession):
    run(db,lambda: execute(db,"EXEC community.usp_CancelReminder @ActorUserId=:actor,@EventId=:event,@Id=:id",dict(actor=current_user.id,event=event_id,id=identifier)).close(),write=True)


@router.put("/{event_id}/rsvp", response_model=RsvpResponse)
def upsert_rsvp(
    event_id: UUID, payload: RsvpRequest, current_user: CurrentUser, db: DbSession
) -> RsvpResponse:
    """Trả lời tham dự. Gọi lại nhiều lần chỉ cập nhật, không tạo dòng trùng (MERGE)."""
    return upsert_rsvp_service(event_id, payload, current_user, db)


@router.post(
    "/{event_id}/gallery",
    response_model=GalleryItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_gallery_item(
    event_id: UUID, payload: GalleryCreateRequest, current_user: CurrentUser, db: DbSession
) -> GalleryItemResponse:
    return add_gallery_item_service(event_id, payload, current_user, db)


@router.get("/{event_id}/gallery", response_model=list[GalleryItemResponse])
def list_gallery(
    event_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 30,
) -> list[GalleryItemResponse]:
    """Thư viện ảnh của sự kiện."""
    return list_gallery_service(event_id, PageParams(page=page, page_size=page_size), current_user, db)


@router.post(
    "/{event_id}/reminders",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reminder(
    event_id: UUID, payload: ReminderCreateRequest, current_user: CurrentUser, db: DbSession
) -> ReminderResponse:
    """Đặt nhắc nhở. Worker gửi vào hộp thư khi tới giờ (usp_DeliverDueReminders)."""
    return create_reminder_service(event_id, payload, current_user, db)
