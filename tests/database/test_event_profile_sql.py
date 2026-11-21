"""Standalone SQL integration; refuses the primary DB, never seeds/drops it."""
import sys,re
from pathlib import Path
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/"apps/backend"),str(ROOT/"database")]


def main():
    from sqlalchemy import create_engine,text
    from sqlalchemy.exc import DBAPIError
    from app.core.database import database_url
    from migrate_event_profile import apply
    name=database_url.database
    if not re.fullmatch(r"[A-Za-z0-9_]+_EventProfile_Test",name or ""):
        raise RuntimeError("Use an isolated _EventProfile_Test database")
    master=create_engine(database_url.set(database="master"),isolation_level="AUTOCOMMIT")
    with master.connect() as c:
        if c.execute(text("SELECT DB_ID(:name)"),dict(name=name)).scalar() is None:c.exec_driver_sql(f"CREATE DATABASE [{name}]").close()
    master.dispose();engine=create_engine(database_url)
    def script(c,path):
        for batch in re.split(r"(?im)^\s*GO\s*(?:--[^\r\n]*)?\r?$",path.read_text(encoding="utf-8-sig").replace("$(DB_NAME)",name)):
            if batch.strip():c.exec_driver_sql(batch).close()
    family,legacy=[str(uuid4()) for _ in range(2)]
    with engine.begin() as c:
        for schema in ("core","genealogy","community","heritage","reports"):
            c.exec_driver_sql(f"IF SCHEMA_ID(N'{schema}') IS NULL EXEC(N'CREATE SCHEMA [{schema}]')").close()
        for path in sorted((ROOT/"database/schema").glob("*.sql")):
            if path.name not in ("00_schemas.sql","10_event_completion.sql"):script(c,path)
        c.execute(text("INSERT core.Families(Id,Name) VALUES(:id,'Event QA')"),dict(id=family))
        c.execute(text("INSERT community.Events(Id,FamilyId,Title,EventDate,Location) VALUES(:id,:f,'Legacy',DATEADD(hour,-2,SYSUTCDATETIME()),'QA')"),dict(id=legacy,f=family))
        if c.execute(text("SELECT COL_LENGTH('community.Events','CompletionEnabled')")).scalar() is not None:
            c.execute(text("UPDATE community.Events SET CompletionEnabled=0 WHERE Id=:id"),dict(id=legacy))
        script(c,ROOT/"database/schema/10_event_completion.sql")
        for folder in ("views","procedures","triggers"):
            for path in sorted((ROOT/"database"/folder).glob("*.sql")):script(c,path)
        apply(c,name);apply(c,name)
        c.execute(text("UPDATE community.Events SET EndDate=DATEADD(hour,-1,SYSUTCDATETIME()) WHERE Id=:id"),dict(id=legacy))
    active,disabled,outside,admin=[str(uuid4()) for _ in range(4)]
    members={}
    with engine.begin() as c:
        for user in (active,disabled,outside,admin):
            c.execute(text("INSERT core.Users(UserId,Email,FullName,PasswordHash,Role,IsActive) VALUES(:id,:email,'QA','test',:role,:active)"),dict(id=user,email=user+"@example.com",role="admin" if user==admin else "member",active=user!=disabled))
            if user in (active,disabled,admin):
                member=str(uuid4());members[user]=member
                c.execute(text("INSERT genealogy.Members(Id,FamilyId,UserId,FullName) VALUES(:id,:f,:u,'QA')"),dict(id=member,f=family,u=user))
    ended,future,current,unknown=[str(uuid4()) for _ in range(4)]
    with engine.begin() as c:
        for identifier,start,end in ((ended,-120,-1),(future,60,120),(current,-30,60),(unknown,-60,None)):
            c.execute(text("INSERT community.Events(Id,FamilyId,Title,EventDate,EndDate,Location) VALUES(:id,:f,'QA',DATEADD(minute,:s,SYSUTCDATETIME()),DATEADD(minute,:e,SYSUTCDATETIME()),'QA')"),dict(id=identifier,f=family,s=start,e=end))
    def deliver():
        with engine.begin() as c:return c.exec_driver_sql("EXEC community.usp_DeliverEndedEvents").scalar()
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda _:deliver(),range(2)))
    def count(c,sql,**params):return c.execute(text(sql),params).scalar()
    with engine.begin() as c:
        assert count(c,"SELECT COUNT(*) FROM community.Notifications WHERE NotificationType='event_ended' AND EventId=:id",id=ended)==2
        for event in (future,current,unknown,legacy):assert count(c,"SELECT COUNT(*) FROM community.Notifications WHERE EventId=:id",id=event)==0
        assert count(c,"SELECT COUNT(*) FROM community.Notifications WHERE UserId IN (:a,:b)",a=disabled,b=outside)==0
        c.execute(text("UPDATE community.Notifications SET ReadAt=SYSUTCDATETIME() WHERE EventId=:id"),dict(id=ended))
    assert deliver()==0
    with engine.begin() as c:
        assert count(c,"SELECT COUNT(*) FROM community.Notifications WHERE EventId=:id AND ReadAt IS NOT NULL",id=ended)==2
        # Rescheduling after delivery never creates a second round.
        c.execute(text("EXEC community.usp_UpdateEventSchedule @ActorUserId=:a,@EventId=:id,@Title='Changed',@EventDate='2020-01-01',@EndDate='2020-01-02',@Location='QA'"),dict(a=admin,id=ended))
        c.execute(text("INSERT community.EventReminders(EventId,ReminderTime,UserId) VALUES(:id,DATEADD(minute,-1,SYSUTCDATETIME()),:u)"),dict(id=current,u=active))
        assert c.exec_driver_sql("EXEC community.usp_DeliverDueReminders").scalar()==1
    assert deliver()==0
    # History validation, CRUD and SQL permissions without touching any existing data.
    def history(actor,resource,action,identifier=None,degree="Degree",end=None):
        with engine.begin() as c:
            result=c.execute(text("EXEC genealogy.usp_ManageHistory @ActorUserId=:a,@MemberId=:m,@Resource=:r,@Action=:action,@Id=:id,@Institution='School',@Degree=:degree,@Company='Company',@Position='Engineer',@StartDate='2020-01-01',@EndDate=:end"),dict(a=actor,m=members[active],r=resource,action=action,id=identifier,degree=degree,end=end))
            return result.mappings().one() if action!="delete" else None
    for resource in ("work","educations"):
        row=history(active,resource,"create");history(active,resource,"update",row["id"] if "id" in row else row["Id"])
        history(active,resource,"delete",row["id"] if "id" in row else row["Id"])
    for actor,degree,end in ((outside,"Degree",None),(active,None,None),(active,"   ",None),(active,"Degree","2019-01-01")):
        try:history(actor,"educations","create",degree=degree,end=end)
        except DBAPIError:pass
        else:raise AssertionError("Invalid/unauthorized history accepted")
    with engine.begin() as c:
        c.execute(text("EXEC community.usp_ManageEvent @ActorUserId=:a,@EventId=:id,@Action='delete'"),dict(a=admin,id=ended))
        assert count(c,"SELECT COUNT(*) FROM community.Notifications WHERE SourceId=:id AND EventId IS NULL",id=ended)==2
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import Session
    from types import SimpleNamespace
    from uuid import UUID
    from app.main import app
    from app.core.database import get_db
    from app.core.security import create_access_token
    def session():
        with Session(engine) as db:yield db
    app.dependency_overrides[get_db]=session
    def headers(user):return {"Authorization":"Bearer "+create_access_token(SimpleNamespace(id=UUID(user)))}
    with TestClient(app) as client:
        response=client.post('/api/events',headers=headers(admin),json=dict(family_id=family,title='API event',location='QA',event_date='2030-01-01T10:00:00+07:00',end_date='2030-01-01T11:00:00+07:00'))
        assert response.status_code==201,response.text
        event=response.json()['event_id']
        assert response.json()['end_date'].startswith('2030-01-01T04:00:00')
        assert client.get('/api/events',headers=headers(active),params=dict(family_id=family,year=2030,month=1,tz_offset=420)).json()[0]['end_date']
        response=client.get('/api/events',headers=headers(active),params=dict(family_id=family,year=2030,month=1,tz_offset=0))
        assert response.status_code==200,response.text
        assert response.json()[0]['end_date']
        assert client.put('/api/events/'+event,headers=headers(admin),json=dict(title='Updated',location='QA',event_date='2030-01-01T03:00:00')).json()['end_date']
        assert client.get('/api/events/'+event,headers=headers(outside)).status_code==403
        profile=client.get('/api/genealogy/me',headers=headers(active)).json()
        assert profile['member']['id']==members[active]
        path='/api/directory/'+profile['member']['id']
        response=client.post(path+'/educations',headers=headers(active),json=dict(institution='API school',degree='Degree',start_date='2020-01-01'))
        assert response.status_code==201,response.text
        detail=client.get(path,headers=headers(active),params=dict(family_id=family)).json()
        assert any(row['institution']=='API school' for row in detail['educations'])
        assert detail['can_edit']
        assert client.post(path+'/work',headers=headers(outside),json=dict(company='Company',position='Engineer',start_date='2020-01-01')).status_code==403
        inbox=client.get('/api/notifications',headers=headers(active)).json()
        assert any(row['notification_type']=='event_ended' for row in inbox['items'])
        assert client.get('/api/notifications').status_code==401
    app.dependency_overrides.clear()
    print("PASS SQL: repeat migration; legacy exclusion; future/current/missing end; concurrent/repeated worker; membership/disabled; read preservation; reschedule; old reminders; deletion; history CRUD/validation/authorization")
    print("PASS actual JWT/API/SQL: event create/update/list/timezone/access; own profile/history; inbox and authentication")


if __name__=="__main__":main()
