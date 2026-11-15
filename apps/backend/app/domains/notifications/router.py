from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user,get_db
from app.domains.genealogy.repository import rows
from app.domains.genealogy.services import run
from app.domains.heritage.repository import execute
from app.domains.identity.models import User

router=APIRouter(prefix="/notifications",tags=["notifications"])
DB=Annotated[Session,Depends(get_db)]
Actor=Annotated[User,Depends(get_current_user)]
ACCESS="""n.UserId=:actor AND EXISTS(SELECT 1 FROM core.Users u WHERE u.UserId=:actor AND u.Role IN ('admin','family_head','member'))
    AND (EXISTS(SELECT 1 FROM core.Users u WHERE u.UserId=:actor AND u.Role='admin')
    OR EXISTS(SELECT 1 FROM genealogy.Members m WHERE m.UserId=:actor AND m.FamilyId=n.FamilyId))"""


@router.get("")
def inbox(db: DB,actor: Actor,page: int=Query(default=1,ge=1),page_size: int=Query(default=20,ge=1,le=100)):
    def operation():
        params=dict(actor=actor.id,offset=(page-1)*page_size,limit=page_size)
        items=rows(db,f"""SELECT n.Id AS id,n.FamilyId AS family_id,n.EventId AS event_id,n.Title AS title,n.Body AS body,
            n.CreatedAt AS created_at,n.ReadAt AS read_at FROM community.Notifications n WHERE {ACCESS}
            ORDER BY n.CreatedAt DESC,n.Id OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY""",**params)
        total=execute(db,f"SELECT COUNT(*) FROM community.Notifications n WHERE {ACCESS}",params).scalar_one()
        unread=execute(db,f"SELECT COUNT(*) FROM community.Notifications n WHERE {ACCESS} AND n.ReadAt IS NULL",params).scalar_one()
        return dict(items=items,total=total,unread=unread,page=page,page_size=page_size)
    return run(db,operation)


@router.get("/reminders")
def upcoming(db: DB,actor: Actor):
    return run(db,lambda: rows(db,"""SELECT TOP(500) r.Id AS id,r.EventId AS event_id,r.ReminderTime AS reminder_time,e.Title AS title
        FROM community.EventReminders r JOIN community.Events e ON e.Id=r.EventId
        WHERE r.Status='pending' AND r.ReminderTime>SYSUTCDATETIME() AND (r.UserId=:actor OR r.UserId IS NULL)
        AND EXISTS(SELECT 1 FROM core.Users u WHERE u.UserId=:actor AND u.Role IN ('admin','family_head','member'))
        AND (EXISTS(SELECT 1 FROM core.Users u WHERE u.UserId=:actor AND u.Role='admin') OR
             EXISTS(SELECT 1 FROM genealogy.Members m WHERE m.UserId=:actor AND m.FamilyId=e.FamilyId))
        ORDER BY r.ReminderTime,r.Id""",actor=actor.id))


@router.patch("/{identifier}/read",status_code=204)
def mark_read(identifier: UUID,db: DB,actor: Actor):
    def operation():
        matched=rows(db,f"SELECT n.Id FROM community.Notifications n WHERE {ACCESS} AND n.Id=:id",actor=actor.id,id=identifier)
        if not matched: raise HTTPException(404,"Không tìm thấy thông báo.")
        execute(db,"UPDATE community.Notifications SET ReadAt=COALESCE(ReadAt,SYSUTCDATETIME()) WHERE Id=:id AND UserId=:actor",dict(id=identifier,actor=actor.id)).close()
    run(db,operation,write=True)


