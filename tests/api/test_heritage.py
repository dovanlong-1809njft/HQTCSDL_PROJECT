"""TV4 API/service contracts with a SQL test double; never connects to SQL Server.

Real JWT verification is used. The double models SQL outcomes, not proof of SQL
authorization/transactions; those require tests/database/tv4.integration.sql.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps/backend"))
os.environ.setdefault("JWT_SECRET_KEY", "tv4-tests-only-key-at-least-32-chars")
from app.core.config import JWT_SECRET_KEY
from app.core.database import get_db
from app.domains.heritage import repository, services
from app.domains.identity.models import User
from app.main import app

FAMILY = UUID(int=101)
OTHER = UUID(int=102)
USER = UUID(int=201)
ITEM = UUID(int=301)
MEMBER = UUID(int=401)
HONOR = UUID(int=501)
TOKEN = "A" * 64
ITEM_ROW = dict(Id=ITEM, FamilyId=FAMILY, CreatedByUserId=USER, Type="story", Title="Ký ức",
                Description=None, Content="Chuyện nhà", MediaUrl=None, CreatedAt="2026-11-13T00:00:00", VersionToken=TOKEN)
HONOR_ROW = dict(Id=HONOR, FamilyId=FAMILY, MemberId=MEMBER, FullName="Thành viên", Title="Đóng góp",
                 Description=None, DateAwarded=None, CreatedAt="2026-11-13T00:00:00", VersionToken=TOKEN)


def sql_error(code):
    return DBAPIError("test", {}, Exception(f"[TV4_SQL:{code}] private SQL details"), False)


class Result:
    def __init__(self, rows=None, scalar=None):
        self.rows = rows or []
        self.value = scalar
    def mappings(self): return self
    def all(self): return self.rows
    def one(self): return self.rows[0]
    def one_or_none(self): return self.rows[0] if self.rows else None
    def scalar_one(self): return self.value
    def close(self): pass


class Database:
    def __init__(self):
        self.role = "member"
        self.calls = []
        self.commits = self.rollbacks = 0
        self.missing = False
        self.error = None
        self.owner = USER
        self.active = True

    def scalar(self, statement):
        # get_current_user uses a real decoded UUID and queries active accounts.
        if USER not in statement.compile().params.values() or not self.active: return None
        return User(id=USER, email="tv4@example.invalid", password_hash="unused", full_name="TV4",
                    role=self.role, is_active=True)

    def execute(self, statement, params):
        sql = str(statement)
        self.calls.append((sql, params))
        if "usp_AssertFamilyAccess" in sql:
            if params["family_id"] != str(FAMILY) and self.role != "admin": raise sql_error(51403)
            if params["manage"] and self.role not in ("admin", "family_head"): raise sql_error(51403)
            return Result()
        if "usp_GetFamilyTreeJson" in sql:
            if params["family_id"] != str(FAMILY) and self.role != "admin": raise sql_error(51403)
            return Result(scalar=json.dumps(dict(family_id=str(FAMILY), nodes=[dict(id=str(MEMBER), label="A", birth_date=None)], edges=[])))
        if "EXEC heritage.usp_" in sql:
            if self.error: raise sql_error(self.error)
            if params.get("expected_version", TOKEN) != TOKEN: raise sql_error(51409)
            if self.missing: raise sql_error(51404)
            if "HeritageItem" in sql and ("Update" in sql or "Delete" in sql) and self.owner != USER and self.role == "member":
                raise sql_error(51403)
            row = dict(HONOR_ROW if "Honor" in sql else ITEM_ROW)
            row.update({{"title": "Title", "content": "Content", "description": "Description"}[key]: value
                        for key, value in params.items() if key in ("title", "content", "description")})
            return Result([row])
        if "core.Families f" in sql: return Result([dict(Id=FAMILY, Name="Gia đình")])
        if "COUNT_BIG" in sql: return Result(scalar=1)
        if "vw_MemberHonorsRanking" in sql:
            return Result([dict(FamilyId=FAMILY, MemberId=MEMBER, FullName="A", HonorCount=0, Rank=1)])
        if "genealogy.Members" in sql: return Result([dict(Id=MEMBER, FullName="A")])
        row = dict(HONOR_ROW if "vw_Honors" in sql else ITEM_ROW)
        if "Id=:id" in sql and (self.missing or params["id"] not in (str(ITEM), str(HONOR))): return Result()
        return Result([row])

    def commit(self): self.commits += 1
    def rollback(self): self.rollbacks += 1


def headers(**claims):
    payload = dict(sub=str(USER), exp=datetime.now(timezone.utc) + timedelta(minutes=10))
    payload.update(claims)
    return {"Authorization": "Bearer " + jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")}


@pytest.fixture
def api():
    db = Database()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client, db
    app.dependency_overrides.clear()


ENDPOINTS = [("get", "/items", None), ("get", f"/items/{ITEM}", None),
             ("post", "/items", dict(type="story", title="A", content="B")),
             ("patch", f"/items/{ITEM}", dict(title="C", expected_version=TOKEN)),
             ("delete", f"/items/{ITEM}", None), ("get", "/honors", None),
             ("get", f"/honors/{HONOR}", None),
             ("post", "/honors", dict(member_id=str(MEMBER), title="A")),
             ("patch", f"/honors/{HONOR}", dict(title="C", expected_version=TOKEN)),
             ("delete", f"/honors/{HONOR}", None), ("get", "/ranking", None),
             ("get", "/members", None), ("get", "/family-tree", None), ("get", "/families", None)]


def request(client, method, path, body=None, family=FAMILY, auth=None):
    options = dict(params=dict(family_id=str(family), expected_version=TOKEN), headers=auth or {})
    if body is not None: options["json"] = body
    return client.request(method, "/api/heritage" + path, **options)


@pytest.mark.parametrize("method,path,body", ENDPOINTS)
def test_every_endpoint_requires_real_jwt(api, method, path, body):
    client, db = api
    assert request(client, method, path, body).status_code == 401
    assert not db.calls


@pytest.mark.parametrize("method,path,body", ENDPOINTS)
def test_guest_cannot_use_tv4(api, method, path, body):
    client, db = api
    db.role = "guest"
    assert request(client, method, path, body, auth=headers()).status_code == 403
    assert not db.calls


@pytest.mark.parametrize("method,path,body", [e for e in ENDPOINTS if e[1] != "/families"])
def test_other_family_procedure_denial_propagates(api, method, path, body):
    client, db = api
    db.role = "family_head"
    assert request(client, method, path, body, family=OTHER, auth=headers()).status_code == 403
    assert db.commits == 0


@pytest.mark.parametrize("claims", [dict(exp=0), dict(sub="bad"), dict(sub=str(UUID(int=999)))])
def test_bad_expired_unknown_jwt(api, claims):
    client, _ = api
    assert request(client, "get", "/items", auth=headers(**claims)).status_code == 401


def test_forged_signature_and_locked_account(api):
    client, db = api
    forged = jwt.encode(dict(sub=str(USER), role="admin"), "wrong-key-at-least-32-characters!!", algorithm="HS256")
    assert request(client, "get", "/items", auth={"Authorization": "Bearer " + forged}).status_code == 401
    db.active = False
    assert request(client, "get", "/items", auth=headers()).status_code == 401


def test_jwt_role_claim_cannot_grant_honors(api):
    client, db = api
    assert request(client, "post", "/honors", dict(member_id=str(MEMBER), title="A"), auth=headers(role="admin")).status_code == 403
    assert db.commits == 0


@pytest.mark.parametrize("payload", [dict(type="story", title=" ", content="B"), dict(type="story", title="A"),
    dict(type="photo", title="A", media_url="javascript:alert(1)"), dict(type="photo", title="A", media_url="//evil.test/a"),
    dict(type="document", title="A"), dict(type="story", title="A", content="B", actor_id=str(USER)),
    dict(type="photo", title="A", media_url="https://a.test/\\evil"),
    dict(type="story", title="A", content="B", family_id=str(OTHER))])
def test_invalid_item_and_mass_assignment(api, payload):
    client, db = api
    assert request(client, "post", "/items", payload, auth=headers()).status_code == 422
    assert not db.calls


def test_create_uses_jwt_actor_bound_values_and_commits(api):
    client, db = api
    title = "'); DROP TABLE heritage.Items;--"
    response = request(client, "post", "/items", dict(type="story", title=title, content="B"), auth=headers())
    assert response.status_code == 201, response.text
    sql, params = db.calls[-1]
    assert params["actor_id"] == str(USER) and params["family_id"] == str(FAMILY)
    assert title not in sql and params["title"] == title
    assert db.commits == 1


def test_partial_patch_preserves_fields_and_version(api):
    client, db = api
    response = request(client, "patch", f"/items/{ITEM}", dict(title="Mới", expected_version=TOKEN), auth=headers())
    assert response.status_code == 200, response.text
    assert db.calls[-1][1]["content"] == "Chuyện nhà"
    assert db.calls[-1][1]["expected_version"] == TOKEN
    assert db.commits == 1


@pytest.mark.parametrize("body", [dict(title=None, expected_version=TOKEN), dict(content=None, expected_version=TOKEN), dict(title="A")])
def test_invalid_partial_payload(api, body):
    client, db = api
    assert request(client, "patch", f"/items/{ITEM}", body, auth=headers()).status_code == 422
    assert db.commits == 0


@pytest.mark.parametrize("action", ["patch", "delete"])
def test_member_cannot_edit_or_delete_other_author(api, action):
    client, db = api
    db.owner = UUID(int=999)
    body = dict(title="C", expected_version=TOKEN) if action == "patch" else None
    assert request(client, action, f"/items/{ITEM}", body, auth=headers()).status_code == 403
    assert db.rollbacks and not db.commits


@pytest.mark.parametrize("code,status", [(51409,409), (51410,409), (51404,404), (51422,422), (1205,503), (99999,500)])
def test_sql_errors_are_sanitized_and_rolled_back(api, code, status):
    client, db = api
    db.error = code
    response = request(client, "post", "/items", dict(type="story", title="A", content="B"), auth=headers())
    assert response.status_code == status
    assert "private SQL" not in response.text
    assert db.rollbacks == 1 and db.commits == 0


def test_missing_item_returns_404(api):
    client, db = api
    db.missing = True
    assert request(client, "get", f"/items/{ITEM}", auth=headers()).status_code == 404


@pytest.mark.parametrize("resource", ["items", "honors", "ranking", "members"])
def test_pagination_family_and_search_are_bound(api, resource):
    client, db = api
    response = client.get(f"/api/heritage/{resource}", params=dict(family_id=str(FAMILY), page=2, page_size=5, q="%_"), headers=headers())
    assert response.status_code == 200, response.text
    assert response.json()["page"] == 2 and response.json()["total"] == 1
    sql, params = db.calls[-1]
    assert params["offset"] == 5 and params["q"] == "%_" and params["family_id"] == str(FAMILY)
    assert "FamilyId=:family_id" in sql and "CHARINDEX" in sql


@pytest.mark.parametrize("params", [dict(page=0), dict(page_size=101), dict(q="x"*201), dict(family_id="bad")])
def test_pagination_validation(api, params):
    client, _ = api
    assert client.get("/api/heritage/items", params=dict(dict(family_id=str(FAMILY)), **params), headers=headers()).status_code == 422


def test_honor_create_patch_delete_for_manager(api):
    client, db = api
    db.role = "family_head"
    for method, path, body, status in [
        ("post", "/honors", dict(member_id=str(MEMBER), title="A"), 201),
        ("patch", f"/honors/{HONOR}", dict(title="B", expected_version=TOKEN), 200),
        ("delete", f"/honors/{HONOR}", None, 204)]:
        response = request(client, method, path, body, auth=headers())
        assert response.status_code == status, response.text
    assert db.commits == 3


def test_tree_parses_json_without_remapping_relationships(api):
    client, _ = api
    response = request(client, "get", "/family-tree", auth=headers())
    assert response.status_code == 200
    assert response.json()["nodes"][0]["id"] == str(MEMBER)
