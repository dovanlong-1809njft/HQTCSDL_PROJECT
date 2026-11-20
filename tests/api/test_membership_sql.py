"""Profile, verification, CRUD and genealogy rules against isolated SQL Server."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from sqlalchemy import event, text

from test_admin import api, sql_database, admin_password_hash, headers, uid, scalar


@pytest.fixture
def membership_api(api):
    client, engine, options = api
    with engine.begin() as connection:
        connection.exec_driver_sql("GRANT EXECUTE ON SCHEMA::genealogy TO task6_backend; GRANT EXECUTE ON OBJECT::heritage.usp_AssertFamilyAccess TO task6_backend").close()
        connection.exec_driver_sql("GRANT EXECUTE ON OBJECT::heritage.usp_UpsertKnowledgeChunk TO task6_backend").close()
    try:
        yield client, engine, options
    finally:
        with engine.begin() as connection:
            for table in ("heritage.KnowledgeChunks","community.EventParticipants","genealogy.ParentChild","genealogy.Marriages","genealogy.MemberClosure","genealogy.Educations","genealogy.WorkHistories","heritage.Honors"):
                connection.exec_driver_sql(f"DELETE FROM {table}").close()


def call(client, method, path, body=None, user=1, family=1001):
    return client.request(method,"/api/genealogy"+path,json=body,headers=headers(user),params={"family_id":uid(family)})


def member(client, name, **values):
    response=call(client,"POST","/members",dict(name=name,**{"branch_id":uid(2001),"birth_date":"1980-01-01","location":"Test place",**values}))
    assert response.status_code==201,response.text
    return response.json()["id"]


@pytest.mark.parametrize("method,path,body",[
    ("GET","/me",None),("PUT","/me",{"name":"Changed"}),
    ("GET","/verification-candidates?family_name=Family%20A&full_name=Target%20A",None),
    ("POST","/verifications",{"member_id":uid(3001)}),
    ("POST","/families",{"name":"Family C"}),
    ("GET","/members",None),("POST","/members",{"name":"New member"}),
    ("GET","/relationships",None),
    ("POST","/relationships/parent-child",{"first_id":uid(3001),"second_id":uid(3002)}),
])
def test_requires_jwt(membership_api,method,path,body):
    client,_,_=membership_api
    assert client.request(method,"/api/genealogy"+path,json=body).status_code==401


def test_profile_updates_only_self_and_rejects_privilege_fields(membership_api):
    client,engine,_=membership_api
    response=call(client,"PUT","/me",{"name":"My updated name","birth_date":"1990-01-02","location":"Test place"},user=9)
    assert response.status_code==200,response.text
    assert response.json()["member"]["name"]=="My updated name"
    assert scalar(engine,"SELECT FullName FROM core.Users WHERE UserId=:id",id=uid(9))=="My updated name"
    assert scalar(engine,"SELECT FullName FROM core.Users WHERE UserId=:id",id=uid(2))=="Head A"
    for extra in ({"role":"admin"},{"user_id":uid(1)},{"branch_id":uid(2002)}):
        assert call(client,"PUT","/me",dict(name="Attempt",**extra),user=9).status_code==422
    assert call(client,"PUT","/me",{"name":"  "},user=9).status_code==422
    assert call(client,"PUT","/me",{"name":"Future","birth_date":"2999-01-01"},user=9).status_code==422


def test_existing_reserved_email_can_login_and_read_profile(membership_api):
    client,engine,_=membership_api
    with engine.begin() as connection:
        connection.execute(text("UPDATE core.Users SET Email='existing@example.invalid' WHERE UserId=:id"),{"id":uid(1)})
    response=client.post('/api/auth/login',json=dict(email='existing@example.invalid',password='Task6-Test-Admin!2026'))
    assert response.status_code==200,response.text
    assert response.json()['user']['email']=='existing@example.invalid'
    auth={'Authorization':'Bearer '+response.json()['access_token']}
    assert client.get('/api/auth/me',headers=auth).status_code==200
    assert client.get('/api/genealogy/me',headers=auth).status_code==200
    assert client.post('/api/auth/login',json=dict(email='existing@example.invalid',password=' Task6-Test-Admin!2026 ')).status_code==401
    assert client.post('/api/auth/login',json=dict(email='not-an-email',password='Password!')).status_code==422
    assert client.post('/api/auth/register',json=dict(full_name='New user',email='new@example.invalid',password='Password!')).status_code==422


def test_candidate_search_and_request_approval_round_trip(membership_api):
    client,engine,_=membership_api
    with engine.begin() as connection:
        connection.execute(text("DELETE core.MemberVerifications WHERE UserId=:id"),{"id":uid(3)})
    response=client.get("/api/genealogy/verification-candidates",params={"family_name":"Family A","full_name":"Target A"},headers=headers(3))
    assert response.status_code==200,response.text
    assert response.json()[0]["id"]==uid(3001)
    assert set(response.json()[0])=={"id","name","family_name","branch_name"}
    response=call(client,"POST","/verifications",{"member_id":uid(3001)},user=3)
    assert response.status_code==201,response.text
    request=response.json()["verifications"][0]
    assert request["status"]=="pending"
    assert call(client,"POST","/verifications",{"member_id":uid(3002)},user=3).status_code==409
    response=client.patch(f'/api/admin/verifications/{request["id"]}/review',json={"decision":"approved"},headers=headers(2))
    assert response.status_code==200,response.text
    assert call(client,"GET","/me",user=3).json()["member"]["id"]==uid(3001)
    assert call(client,"POST","/verifications",{"member_id":uid(3002)},user=3).status_code==409


def test_family_branch_member_crud_and_constraints(membership_api):
    client,engine,_=membership_api
    family=call(client,"POST","/families",{"name":"Family C"}).json()["id"]
    assert client.put(f"/api/genealogy/families/{family}",headers=headers(),json={"name":"Updated family"}).status_code==200
    assert client.delete(f"/api/genealogy/families/{family}",headers=headers()).status_code==204
    assert call(client,"DELETE",f"/families/{uid(1001)}").status_code==409
    branch=call(client,"POST","/branches",{"name":"New branch"}).json()["id"]
    person=member(client,"New person",branch_id=branch)
    assert call(client,"DELETE",f"/branches/{branch}").status_code==409
    assert call(client,"PUT",f"/members/{person}",{"name":"Renamed person","branch_id":branch,"birth_date":"2000-01-01","location":"Test place"}).status_code==200
    assert call(client,"PUT",f"/branches/{branch}",{"name":"Renamed branch"}).status_code==200
    assert call(client,"POST","/branches",{"name":"Renamed branch"}).status_code==409
    assert call(client,"DELETE",f"/members/{person}").status_code==204
    assert call(client,"DELETE",f"/branches/{branch}").status_code==204
    assert call(client,"DELETE",f"/members/{uid(3014)}").status_code==409
    assert call(client,"POST","/members",{"name":"Wrong branch","branch_id":uid(2003),"birth_date":"1980-01-01","location":"Test place"}).status_code==422
    assert scalar(engine,"SELECT COUNT(*) FROM reports.AuditLog WHERE Action LIKE 'genealogy.%'")>=8


@pytest.mark.parametrize("user,family",[(9,1001),(3,1001),(6,1001),(2,1002),(4,1001)])
def test_write_denied_for_role_or_foreign_family(membership_api,user,family):
    client,engine,_=membership_api
    before=scalar(engine,"SELECT COUNT(*) FROM genealogy.Members")
    assert call(client,"POST","/members",{"name":"Forbidden","branch_id":uid(2001),"birth_date":"1980-01-01","location":"Test place"},user=user,family=family).status_code==403
    assert scalar(engine,"SELECT COUNT(*) FROM genealogy.Members")==before


def test_head_cannot_move_members_to_bypass_branch_approval(membership_api):
    client,engine,_=membership_api
    assert call(client,"PUT",f"/members/{uid(3002)}",{"name":"Target B","branch_id":uid(2001),"birth_date":"1980-01-01","location":"Test place"},user=2).status_code==403
    assert call(client,"PUT",f"/members/{uid(3010)}",{"name":"Head A","branch_id":uid(2002),"birth_date":"1980-01-01","location":"Test place"},user=2).status_code==403
    assert str(scalar(engine,"SELECT BranchId FROM genealogy.Members WHERE Id=:id",id=uid(3010))).lower()==uid(2001)
    assert call(client,"POST","/members",{"name":"New in own branch","branch_id":uid(2001),"birth_date":"1980-01-01","location":"Test place"},user=2).status_code==201
    assert call(client,"POST","/branches",{"name":"Unmanaged new branch"},user=2).status_code==403
    assert call(client,"PUT",f"/branches/{uid(2001)}",{"name":"Renamed own branch"},user=2).status_code==200
    own=call(client,"GET","/members",user=2).json()["items"]
    assert next(row for row in own if row["id"]==uid(3001))["can_manage"]
    assert not next(row for row in own if row["id"]==uid(3002))["can_manage"]
    assert call(client,"POST","/relationships/parent-child",{"first_id":uid(3001),"second_id":uid(3002)},user=2).status_code==403
    assert call(client,"POST","/relationships/parent-child",{"first_id":uid(3002),"second_id":uid(3001)},user=2).status_code==201


def test_relationship_rules_and_closure_after_removal(membership_api):
    client,_,_=membership_api
    a,b,c,d=[member(client,name) for name in ("Ancestor","Parent one","Parent two","Child")]
    def edge(first,second,kind="parent-child"):
        return call(client,"POST","/relationships/"+kind,dict(first_id=first,second_id=second,married_date="2020-01-01" if kind=="marriages" else None))
    assert edge(a,b).status_code==201
    assert edge(a,c).status_code==201
    bd=edge(b,d).json()["id"]
    cd=edge(c,d).json()["id"]
    assert edge(a,b).status_code==409
    assert edge(d,a).status_code==422
    assert edge(a,d).status_code==422
    assert edge(b,c,"marriages").status_code==422
    assert edge(a,a,"marriages").status_code==422
    assert edge(a,uid(3003)).status_code==422
    assert call(client,"DELETE",f"/members/{b}").status_code==409
    path=f"/api/genealogy/relationships?family_id={uid(1001)}&member_id={d}"
    assert {r["id"]:r["depth"] for r in client.get(path,headers=headers()).json()["ancestors"]}[a]==2
    descendants=client.get(f"/api/genealogy/relationships?family_id={uid(1001)}&member_id={a}",headers=headers()).json()["descendants"]
    assert {row["id"]:row["depth"] for row in descendants}[d]==2
    assert all(set(row)=={"id","name","depth"} for row in descendants)
    assert call(client,"DELETE",f"/relationships/parent-child/{bd}").status_code==204
    ancestors=client.get(path,headers=headers()).json()["ancestors"]
    assert a in {r["id"] for r in ancestors} and b not in {r["id"] for r in ancestors}
    assert call(client,"DELETE",f"/relationships/parent-child/{cd}").status_code==204
    assert client.get(path,headers=headers()).json()["ancestors"]==[]
    wedding=edge(b,d,"marriages")
    assert wedding.status_code==201,wedding.text
    assert edge(d,b,"marriages").status_code==409
    assert edge(b,d).status_code==422
    assert call(client,"DELETE",f'/relationships/marriages/{wedding.json()["id"]}').status_code==204


def test_failed_audit_rolls_back_data(membership_api):
    client,engine,options=membership_api
    options["fail_audit"]=True
    before=scalar(engine,"SELECT COUNT(*) FROM genealogy.Members")
    assert call(client,"POST","/members",{"name":"Must roll back","branch_id":uid(2001),"birth_date":"1980-01-01","location":"Test place"}).status_code==500
    assert scalar(engine,"SELECT COUNT(*) FROM genealogy.Members")==before


def test_concurrent_duplicate_edges_leave_one_row(membership_api):
    client,engine,_=membership_api
    a,b=member(client,"Concurrent parent"),member(client,"Concurrent child")
    def insert(_):
        return call(client,"POST","/relationships/parent-child",dict(first_id=a,second_id=b)).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(insert,range(2)))==[201,409]
    assert scalar(engine,"SELECT COUNT(*) FROM genealogy.ParentChild WHERE ParentId=:a AND ChildId=:b",a=a,b=b)==1


def test_index_write_cannot_leave_a_deleted_member_source(membership_api,monkeypatch):
    from app.domains.ai_assistant import services
    client,engine,_=membership_api
    identifier=member(client,"Index race source")
    indexing,release=Event(),Event()
    def embedding(_):
        indexing.set()
        assert release.wait(10)
        return [0.1,0.2]
    monkeypatch.setattr(services,"generate_embedding",embedding)
    def index():
        return client.post('/api/ai/chunks',headers=headers(),json=dict(family_id=uid(1001),source_type='member',source_id=identifier,chunk_text='Index race source'))
    def short_delete_timeout(conn,cursor,statement,parameters,context,executemany):
        if 'usp_ManageRecord' in statement:
            cursor.execute('SET LOCK_TIMEOUT 250')
    event.listen(engine,'before_cursor_execute',short_delete_timeout)
    with ThreadPoolExecutor(max_workers=1) as pool:
        indexing_task=pool.submit(index)
        try:
            assert indexing.wait(10)
            assert call(client,"DELETE",f"/members/{identifier}").status_code==503
        finally:
            event.remove(engine,'before_cursor_execute',short_delete_timeout)
            release.set()
        response=indexing_task.result(timeout=15)
        assert response.status_code==201,response.text
        assert call(client,"DELETE",f"/members/{identifier}").status_code==409
    assert scalar(engine,"SELECT COUNT(*) FROM genealogy.Members WHERE Id=:id",id=identifier)==1
