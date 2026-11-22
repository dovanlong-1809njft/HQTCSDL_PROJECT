from datetime import datetime,timedelta,timezone
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from threading import Event
import sys
from pathlib import Path
from sqlalchemy.orm import Session

import pytest
from sqlalchemy import text

from test_admin import api,sql_database,admin_password_hash,headers,uid,scalar


@pytest.fixture
def feature_api(api):
    client,engine,options=api
    with engine.begin() as conn:
        conn.exec_driver_sql("GRANT SELECT,EXECUTE ON SCHEMA::genealogy TO task6_backend; GRANT SELECT,EXECUTE ON SCHEMA::community TO task6_backend; GRANT SELECT,EXECUTE ON SCHEMA::heritage TO task6_backend; GRANT UPDATE ON community.Notifications TO task6_backend").close()
        for table in ('Events','EventReminders','EventGalleries','Comments','ReportedContents'):
            conn.exec_driver_sql(f'GRANT INSERT ON community.{table} TO task6_backend').close()
    try: yield client,engine,options
    finally:
        with engine.begin() as conn:
            for table in ('community.Notifications','heritage.KnowledgeChunks','community.ReportedContents','community.Posts','community.Events','genealogy.ParentChild','genealogy.MemberClosure','genealogy.Educations','genealogy.WorkHistories'):
                conn.exec_driver_sql('DELETE FROM '+table).close()


def request(client,method,path,body=None,user=9,**params):
    return client.request(method,'/api'+path,json=body,headers=headers(user),params=params)


def create_event(client):
    when=datetime.now(timezone.utc)+timedelta(days=7)
    response=request(client,'POST','/events',dict(family_id=uid(1001),title='Upcoming test event',location='Test place',event_date=when.isoformat()),user=2)
    assert response.status_code==201,response.text
    return response.json()['event_id'],when


@pytest.mark.parametrize('path',['/directory?family_id='+uid(1001),'/directory/'+uid(3014)+'?family_id='+uid(1001),'/notifications','/notifications/reminders','/events/'+uid(9001)+'/participants'])
def test_new_reads_require_authentication(feature_api,path):
    assert feature_api[0].get('/api'+path).status_code==401


def test_directory_filters_and_history_authorization(feature_api):
    client,engine,_=feature_api
    with engine.begin() as conn:
        conn.execute(text("UPDATE genealogy.Members SET Location='District test' WHERE Id=:id"),dict(id=uid(3014)))
    for resource,body in [('educations',dict(institution='University test',degree='Engineering',start_date='2015-01-01',end_date='2019-01-01')),('work',dict(company='Company test',position='Engineer',start_date='2020-01-01'))]:
        path=f'/directory/{uid(3014)}/{resource}'
        assert request(client,'POST',path,body,user=11).status_code==403
        response=request(client,'POST',path,body)
        assert response.status_code==201,response.text
        identifier=response.json()['id']
        assert request(client,'PUT',path+'/'+identifier,body,user=2).status_code==200
        assert request(client,'PUT',f'/directory/{uid(3002)}/{resource}/{identifier}',body,user=1).status_code==404
    response=request(client,'GET','/directory',family_id=uid(1001),occupation='Engineer',education='Engineering',location='District',current_job=True)
    assert response.status_code==200,response.text
    assert [r['id'] for r in response.json()['items']]==[uid(3014)]
    assert request(client,'GET','/directory',family_id=uid(1002)).status_code==403
    assert request(client,'GET',f'/directory/{uid(3003)}',family_id=uid(1001)).status_code==404
    assert request(client,'POST',f'/directory/{uid(3014)}/work',dict(company='X',position='Y',start_date='2020-01-01',end_date='2010-01-01')).status_code==422
    detail=request(client,'GET',f'/directory/{uid(3014)}',family_id=uid(1001)).json()
    assert detail['can_edit'] and len(detail['work'])==1 and len(detail['educations'])==1
    assert request(client,'DELETE',f'/directory/{uid(3014)}/work/'+detail['work'][0]['id']).status_code==204
    result=request(client,'GET','/directory',family_id=uid(1001),page=999)
    assert result.json()['items']==[] and result.json()['total']>0


def test_posts_announcements_reactions_and_owner_changes(feature_api):
    client,engine,_=feature_api
    body=dict(family_id=uid(1001),content='Family news',media=[dict(url='https://example.com/a,b.jpg')])
    assert request(client,'POST','/community/posts',dict(body,is_announcement=True)).status_code==403
    announcement=request(client,'POST','/community/posts',dict(body,is_announcement=True),user=2)
    assert announcement.status_code==201,announcement.text
    response=request(client,'POST','/community/posts',body)
    assert response.status_code==201,response.text
    post=response.json()['post_id']
    assert response.json()['media_urls']==['https://example.com/a,b.jpg']
    assert request(client,'PUT',f'/community/posts/{post}',dict(content='Other edit',media=[]),user=2).status_code==403
    response=request(client,'PUT',f'/community/posts/{post}',dict(content='Updated news',media=[]))
    assert response.status_code==200 and response.json()['content']=='Updated news'
    assert request(client,'PUT',f'/community/posts/{post}/reactions',dict(type='Love')).status_code==200
    assert request(client,'GET',f'/community/posts/{post}').json()['my_reaction']=='Love'
    comment=request(client,'POST',f'/community/posts/{post}/comments',dict(content='Comment'))
    assert comment.status_code==201,comment.text
    cid=comment.json()['id']
    assert request(client,'PUT',f'/community/comments/{cid}',dict(content='Stolen'),user=11).status_code==403
    assert request(client,'PUT',f'/community/comments/{cid}',dict(content='Edited comment')).status_code==204
    assert request(client,'POST','/community/reports',dict(target_id=post,target_type='post',reason='Test report'),user=2).status_code==201
    assert request(client,'DELETE',f'/community/posts/{post}').status_code==204
    assert scalar(engine,'SELECT COUNT(*) FROM community.Comments WHERE PostId=:id',id=post)==0
    assert scalar(engine,"SELECT COUNT(*) FROM community.ReportedContents WHERE TargetId=:id AND Status='pending'",id=post)==0
    assert request(client,'GET',f'/community/posts/{post}').status_code==404


def test_events_participants_gallery_and_reminders(feature_api):
    client,_,_=feature_api
    event,when=create_event(client)
    own=dict(member_id=uid(3014),rsvp_status='Going')
    assert request(client,'PUT',f'/events/{event}/rsvp',own).status_code==200
    assert request(client,'GET',f'/events/{event}').json()['my_rsvp']=='Going'
    assert request(client,'PUT',f'/events/{event}/participants/{uid(3002)}',dict(member_id=uid(3002),rsvp_status='Pending')).status_code==403
    assert request(client,'PUT',f'/events/{event}/participants/{uid(3002)}',dict(member_id=uid(3002),rsvp_status='Pending'),user=2).status_code==204
    participants=request(client,'GET',f'/events/{event}/participants').json()
    assert participants['total']==2 and participants['counts']['Going']==1
    image=request(client,'POST',f'/events/{event}/gallery',dict(media_url='https://example.com/event.jpg')).json()
    assert request(client,'DELETE',f'/events/{event}/gallery/'+image['id'],user=6).status_code==403
    assert request(client,'DELETE',f'/events/{event}/gallery/'+image['id']).status_code==204
    assert request(client,'POST',f'/events/{event}/gallery',dict(media_url='javascript:alert(1)')).status_code==422
    remind=dict(reminder_time=(when-timedelta(hours=1)).isoformat())
    assert request(client,'POST',f'/events/{event}/reminders',dict(remind,for_family=True)).status_code==403
    response=request(client,'POST',f'/events/{event}/reminders',remind)
    assert response.status_code==201,response.text
    reminder=response.json()['id']
    assert response.json()['user_id']==uid(9)
    assert request(client,'GET',f'/events/{event}/reminders',user=11).json()==[response.json()]
    assert request(client,'DELETE',f'/events/{event}/reminders/{reminder}',user=3).status_code==403
    assert request(client,'DELETE',f'/events/{event}/reminders/{reminder}').status_code==204
    assert request(client,'POST',f'/events/{event}/reminders',dict(reminder_time=(when+timedelta(hours=1)).isoformat())).status_code==422
    assert request(client,'DELETE',f'/events/{event}',user=6).status_code==403
    assert request(client,'DELETE',f'/events/{event}',user=2).status_code==204


def test_post_edit_preserves_retained_photo_ids_and_reports(feature_api):
    client,engine,_=feature_api
    urls=['https://example.com/Photo.jpg','https://example.com/photo.jpg']
    media=[dict(url=url) for url in urls]
    created=request(client,'POST','/community/posts',dict(family_id=uid(1001),content='Original caption',media=media))
    assert created.status_code==201,created.text
    post=created.json()['post_id']
    with engine.connect() as conn:
        ids={row.MediaUrl:str(row.Id) for row in conn.execute(text('SELECT Id,MediaUrl FROM community.PostMedia WHERE PostId=:id'),dict(id=post))}
    reports=[]
    for url in urls:
        response=request(client,'POST','/community/reports',dict(target_id=ids[url],target_type='photo',reason='Needs review'),user=2)
        assert response.status_code==201,response.text
        reports.append(response.json()['id'])
    response=request(client,'PUT',f'/community/posts/{post}',dict(content='New caption',media=media))
    assert response.status_code==200,response.text
    for url,report in zip(urls,reports):
        assert scalar(engine,'SELECT MediaUrl FROM community.PostMedia WHERE Id=:id',id=ids[url])==url
        assert scalar(engine,'SELECT Status FROM community.ReportedContents WHERE Id=:id',id=report)=='pending'
    replacement='https://example.com/new.jpg'
    response=request(client,'PUT',f'/community/posts/{post}',dict(content='One photo removed',media=[media[0],dict(url=replacement)]))
    assert response.status_code==200,response.text
    assert set(response.json()['media_urls'])=={urls[0],replacement}
    assert scalar(engine,'SELECT MediaUrl FROM community.PostMedia WHERE Id=:id',id=ids[urls[0]])==urls[0]
    assert scalar(engine,'SELECT Status FROM community.ReportedContents WHERE Id=:id',id=reports[0])=='pending'
    assert scalar(engine,'SELECT COUNT(*) FROM community.PostMedia WHERE Id=:id',id=ids[urls[1]])==0
    assert scalar(engine,'SELECT Status FROM community.ReportedContents WHERE Id=:id',id=reports[1])=='resolved'
    assert request(client,'DELETE',f'/community/posts/{post}').status_code==204
    assert scalar(engine,'SELECT Status FROM community.ReportedContents WHERE Id=:id',id=reports[0])=='resolved'


@pytest.mark.parametrize('for_family',[False,True])
def test_reminder_creation_locks_event_until_insert_commits(feature_api,monkeypatch,for_family):
    from app.domains.events import repository
    client,engine,_=feature_api
    event,when=create_event(client)
    ready,release=Event(),Event()
    original=repository.create_reminder
    def paused_insert(db,**kwargs):
        ready.set()
        assert release.wait(10),'Timed out waiting for concurrent update'
        return original(db,**kwargs)
    monkeypatch.setattr(repository,'create_reminder',paused_insert)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(request,client,'POST',f'/events/{event}/reminders',dict(reminder_time=(when-timedelta(hours=1)).isoformat(),for_family=for_family),user=2 if for_family else 9)
        try:
            assert ready.wait(10),'Reminder request did not reach insert'
            with engine.begin() as conn:
                result=conn.execute(text('''SET NOCOUNT ON; SET LOCK_TIMEOUT 500;
                    BEGIN TRY
                        UPDATE community.Events SET EventDate=:new_date WHERE Id=:id;
                        SELECT 0;
                    END TRY
                    BEGIN CATCH
                        IF ERROR_NUMBER()<>1222 THROW;
                        SELECT ERROR_NUMBER();
                    END CATCH'''),dict(id=event,new_date=(when-timedelta(days=1)).replace(tzinfo=None))).scalar_one()
            assert result==1222,'Event update bypassed the reminder transaction lock'
        finally:
            release.set()
        response=future.result(timeout=10)
    assert response.status_code==201,response.text
    response=request(client,'PUT',f'/events/{event}',dict(title='Earlier event',location='Test place',event_date=(when-timedelta(days=1)).isoformat()),user=2)
    assert response.status_code==409,response.text
    assert request(client,'DELETE',f'/events/{event}/reminders/'+future.result().json()['id'],user=2 if for_family else 9).status_code==204
    assert request(client,'PUT',f'/events/{event}',dict(title='Earlier event',location='Test place',event_date=(when-timedelta(days=1)).isoformat()),user=2).status_code==200
    response=request(client,'POST',f'/events/{event}/reminders',dict(reminder_time=(when-timedelta(hours=1)).isoformat()))
    assert response.status_code==422,response.text


def test_month_filter_respects_phone_timezone(feature_api):
    client,_,_=feature_api
    response=request(client,'POST','/events',dict(family_id=uid(1001),title='New month in Vietnam',location='Test place',event_date='2027-01-01T00:30:00+07:00'),user=2)
    assert response.status_code==201,response.text
    identifier=response.json()['event_id']
    rows=request(client,'GET','/events',family_id=uid(1001),year=2027,month=1,tz_offset=420).json()
    assert identifier in [r['event_id'] for r in rows]
    assert identifier not in [r['event_id'] for r in request(client,'GET','/events',family_id=uid(1001),year=2027,month=1).json()]


def test_worker_inbox_is_exactly_once_and_private(feature_api):
    client,engine,_=feature_api
    event,when=create_event(client)
    reminder=request(client,'POST',f'/events/{event}/reminders',dict(reminder_time=(when-timedelta(hours=1)).isoformat())).json()['id']
    with engine.begin() as conn:
        conn.execute(text('UPDATE community.EventReminders SET ReminderTime=DATEADD(MINUTE,-1,SYSUTCDATETIME()) WHERE Id=:id'),dict(id=reminder))
    def dispatch(_):
        with engine.begin() as conn: return conn.exec_driver_sql('EXEC community.usp_DeliverDueReminders').scalar_one()
    with ThreadPoolExecutor(max_workers=2) as pool: assert sum(pool.map(dispatch,range(2)))==1
    inbox=request(client,'GET','/notifications').json()
    assert inbox['total']==1 and inbox['unread']==1
    assert request(client,'GET','/notifications',user=2).json()['total']==0
    nid=inbox['items'][0]['id']
    assert request(client,'PATCH',f'/notifications/{nid}/read',user=2).status_code==404
    assert request(client,'PATCH',f'/notifications/{nid}/read').status_code==204
    assert request(client,'GET','/notifications').json()['unread']==0
    assert request(client,'DELETE',f'/events/{event}',user=2).status_code==204
    assert request(client,'GET','/notifications').json()['items'][0]['event_id'] is None
    with engine.begin() as conn:
        conn.execute(text("UPDATE core.Users SET Role='guest' WHERE UserId=:id"),dict(id=uid(9)))
    assert request(client,'GET','/notifications').json()['total']==0


def test_cancelled_reminders_are_not_scheduled_or_dispatched(feature_api,monkeypatch):
    client,engine,_=feature_api
    event,when=create_event(client)
    rid=request(client,'POST',f'/events/{event}/reminders',dict(reminder_time=(when-timedelta(hours=1)).isoformat())).json()['id']
    assert rid in [r['id'] for r in request(client,'GET','/notifications/reminders').json()]
    assert request(client,'GET','/notifications/reminders',user=2).json()==[]
    assert request(client,'DELETE',f'/events/{event}/reminders/{rid}').status_code==204
    assert request(client,'GET','/notifications/reminders').json()==[]
    with engine.begin() as conn:
        conn.execute(text('UPDATE community.EventReminders SET ReminderTime=DATEADD(MINUTE,-1,SYSUTCDATETIME()) WHERE Id=:id'),dict(id=rid))
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'apps/worker'))
    from jobs import event_reminder
    monkeypatch.setattr(event_reminder,'SessionLocal',lambda:Session(bind=engine))
    monkeypatch.setattr(event_reminder,'database_access',nullcontext)
    assert event_reminder.run_once()==0
    assert request(client,'GET','/notifications').json()['total']==0

