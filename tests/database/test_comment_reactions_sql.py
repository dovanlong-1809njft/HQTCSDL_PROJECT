"""Standalone integration check. Refuses any database not ending _Reactions_Test.

Uses test fixtures only, leaves the separate test database for inspection, and
never connects to the application's database. No DROP, reset or seed scripts.
"""
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "apps/backend"), str(ROOT / "database")]


def main():
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import DBAPIError
    from app.core.database import database_url
    from migrate_reactions import apply

    database = database_url.database
    if not database or not re.fullmatch(r"[A-Za-z0-9_]+_Reactions_Test", database):
        raise RuntimeError("Set MSSQL_DB to an isolated name ending _Reactions_Test")
    master = create_engine(database_url.set(database="master"), isolation_level="AUTOCOMMIT")
    with master.connect() as connection:
        if connection.execute(text("SELECT DB_ID(:name)"), {"name":database}).scalar() is None:
            connection.exec_driver_sql(f"CREATE DATABASE [{database}]").close()
    master.dispose()
    engine = create_engine(database_url)
    with engine.begin() as c:
        for schema in ("core","genealogy","community","heritage"):
            c.exec_driver_sql(f"IF SCHEMA_ID(N'{schema}') IS NULL EXEC(N'CREATE SCHEMA [{schema}]')").close()
        for name in ("01_core.sql","02_genealogy.sql","03_community_events.sql"):
            script=(ROOT/"database/schema"/name).read_text(encoding="utf-8-sig").replace("$(DB_NAME)",database)
            for batch in re.split(r"(?im)^\s*GO\s*$",script):
                if batch.strip(): c.exec_driver_sql(batch).close()
        c.exec_driver_sql("IF COL_LENGTH('community.Posts','IsAnnouncement') IS NULL ALTER TABLE community.Posts ADD IsAnnouncement BIT NOT NULL DEFAULT 0").close()
        for folder,name in (("views","03_community_views.sql"),("procedures","03_community_procs.sql")):
            script=(ROOT/"database"/folder/name).read_text(encoding="utf-8-sig").replace("$(DB_NAME)",database)
            for batch in re.split(r"(?im)^\s*GO\s*$",script):
                if batch.strip():c.exec_driver_sql(batch).close()
        # Use the actual family authorization procedure, not a stub.
        source=(ROOT/"database/procedures/04_heritage_procs.sql").read_text(encoding="utf-8-sig")
        procedure=source[source.index("CREATE OR ALTER PROCEDURE heritage.usp_AssertFamilyAccess"):source.index("CREATE OR ALTER PROCEDURE heritage.usp_ValidateHeritageItem")]
        c.exec_driver_sql(re.split(r"(?im)^GO\s*$",procedure)[0]).close()
        c.exec_driver_sql("IF DATABASE_PRINCIPAL_ID('role_backend') IS NULL CREATE ROLE role_backend").close()
        apply(c)
        apply(c)  # Repeatability, no data reset.
    family, post, comment, first, second, outsider = [str(uuid4()) for _ in range(6)]
    with engine.begin() as c:
        c.execute(text("INSERT core.Families(Id,Name) VALUES(:id,N'Isolated reaction test')"),{"id":family})
        for user in (first,second,outsider):
            c.execute(text("INSERT core.Users(UserId,Email,PasswordHash,FullName,Role) VALUES(:id,:email,'test',N'Test member','member')"),{"id":user,"email":user+"@example.invalid"})
        for user in (first,second):
            c.execute(text("INSERT genealogy.Members(FamilyId,UserId,FullName) VALUES(:family,:user,N'Test member')"),{"family":family,"user":user})
        c.execute(text("INSERT community.Posts(Id,FamilyId,UserId,Content) VALUES(:id,:family,:user,N'Test')"),{"id":post,"family":family,"user":first})
        c.execute(text("INSERT community.Comments(Id,PostId,UserId,Content) VALUES(:id,:post,:user,N'Test')"),{"id":comment,"post":post,"user":first})

    def react(user, kind, identifier=comment):
        with engine.begin() as c:
            c.execute(text("EXEC community.usp_SetCommentReaction @CommentId=:id,@ActorUserId=:actor,@Type=:kind"),{"id":identifier,"actor":user,"kind":kind}).close()
    def rows():
        with engine.connect() as c:
            return c.execute(text("SELECT UserId,Type FROM community.CommentReactions WHERE CommentId=:id"),{"id":comment}).all()
    react(first,"Like"); react(first,"Love")
    assert len(rows())==1 and rows()[0][1]=="Love"
    react(second,"Sad"); assert len(rows())==2
    react(first,None); assert len(rows())==1
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(lambda _:react(first,"Haha"),range(18)))
    assert len(rows())==2
    # Real API -> service -> SQL integration, with session/actor overrides only.
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import Session
    from types import SimpleNamespace
    from uuid import UUID
    from app.domains.community.router import router
    from app.core.database import get_db
    from app.core.dependencies import get_current_user
    app=FastAPI()
    app.include_router(router,prefix="/api")
    def database_session():
        with Session(engine) as db:yield db
    actor=SimpleNamespace(id=UUID(first),role="member",is_active=True)
    app.dependency_overrides[get_db]=database_session
    app.dependency_overrides[get_current_user]=lambda:actor
    with TestClient(app) as client:
        response=client.put(f"/api/community/comments/{comment}/reactions",json={"type":"Angry"})
        assert response.status_code==200,response.text
        assert response.json()["reaction_counts"]=={"Angry":1,"Sad":1}
        response=client.get(f"/api/community/posts/{post}/comments")
        assert response.status_code==200,response.text
        assert response.json()[0]["my_reaction"]=="Angry"
        actor.id=UUID(second)
        assert client.get(f"/api/community/posts/{post}/comments").json()[0]["my_reaction"]=="Sad"
        for kind in ("Like","Love",None):
            response=client.put(f"/api/community/posts/{post}/reactions",json={"type":kind})
            assert response.status_code==200,response.text
            assert response.json()["reaction_counts"]==({kind:1} if kind else {})
            assert client.get(f"/api/community/posts/{post}").json()["my_reaction"]==kind
        actor.id=UUID(outsider)
        assert client.put(f"/api/community/comments/{comment}/reactions",json={"type":"Like"}).status_code==403
        app.dependency_overrides.pop(get_current_user)
        assert client.put(f"/api/community/comments/{comment}/reactions",json={"type":"Like"}).status_code==401
    for user,kind,identifier in ((outsider,"Like",comment),(first,"Like",str(uuid4())),(first,"invalid",comment)):
        try: react(user,kind,identifier)
        except DBAPIError: pass
        else: raise AssertionError("Unauthorized/missing/invalid reaction was accepted")
    assert len(rows())==2
    with engine.begin() as c:
        c.execute(text("DELETE community.Comments WHERE Id=:id"),{"id":comment})
    assert not rows()
    # Also test the Post -> Comment -> CommentReaction cascade.
    with engine.begin() as c:
        c.execute(text("INSERT community.Comments(Id,PostId,UserId,Content) VALUES(:id,:post,:user,N'Test')"),{"id":comment,"post":post,"user":first})
    react(first,"Wow")
    with engine.begin() as c:
        c.execute(text("DELETE community.Posts WHERE Id=:id"),{"id":post})
    assert not rows()
    engine.dispose()
    print("PASS: rerun migration; change/remove; two users; concurrent uniqueness; authorization; missing comment; CHECK; delete cascades; real API/SQL post+comment persistence/summaries; JWT required. Isolated test database retained.")


if __name__ == "__main__":
    main()
