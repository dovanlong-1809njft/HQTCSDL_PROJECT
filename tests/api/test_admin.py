"""Task 6: real SQL Server + FastAPI, using an isolated database and backend grants.

Run from the project root with TASK6_SQL_SERVER=localhost; see tests/api/README.md.
All database fixtures are T-SQL in tests/database/task6.integration.sql.
"""
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "backend"))
os.environ.setdefault("JWT_SECRET_KEY", "task6-tests-only-secret-key-at-least-32-characters")

from app.core.config import JWT_SECRET_KEY  # noqa: E402
from app.core.dependencies import get_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402


def uid(number: int) -> str:
    return str(UUID(int=number))


def execute_script(connection, script: str, database: str) -> None:
    for batch in re.split(r"(?im)^\s*GO\s*(?:--[^\r\n]*)?\r?$", script.replace("$(DB_NAME)", database)):
        if batch.strip():
            result = connection.exec_driver_sql(batch)
            result.close()


@pytest.fixture(scope="session")
def sql_database():
    server = os.getenv("TASK6_SQL_SERVER")
    if not server:
        pytest.skip("Set TASK6_SQL_SERVER to run the real SQL Server integration tests.")
    name = "FamilyConnect_Task6Test_" + uuid4().hex
    port = os.getenv("TASK6_SQL_PORT")
    url = URL.create("mssql+mssqlpython", host=server,
                     port=int(port) if port else None, database="master",
                     query={"Trusted_Connection": "yes", "TrustServerCertificate": "yes"})
    master = create_engine(url, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    engine = None
    created = False
    try:
        with master.connect() as connection:
            connection.exec_driver_sql(f"CREATE DATABASE [{name}]").close()
        created = True
        engine = create_engine(url.set(database=name), poolclass=NullPool)
        with engine.begin() as connection:
            for folder in ("schema", "views", "procedures", "triggers"):
                for path in sorted((ROOT / "database" / folder).glob("*.sql")):
                    execute_script(connection, path.read_text(encoding="utf-8-sig"), name)
            # Idempotent deployment of the task 6 procedures.
            execute_script(connection, (ROOT / "database/procedures/06_admin_procs.sql").read_text(encoding="utf-8"), name)
        yield engine, name
    finally:
        if engine is not None:
            engine.dispose()
        if created:
            assert re.fullmatch(r"FamilyConnect_Task6Test_[0-9a-f]{32}", name)
            with master.connect() as connection:
                connection.exec_driver_sql(f"ALTER DATABASE [{name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE").close()
                connection.exec_driver_sql(f"DROP DATABASE [{name}]").close()
        master.dispose()


@pytest.fixture(scope="session")
def admin_password_hash():
    return hash_password("Task6-Test-Admin!2026")


@pytest.fixture
def api(sql_database, admin_password_hash):
    engine, name = sql_database
    with engine.begin() as connection:
        execute_script(connection, (ROOT / "tests/database/task6.integration.sql").read_text(encoding="utf-8"), name)
        connection.execute(text("UPDATE core.Users SET PasswordHash = :hash WHERE UserId = :id"),
                           {"hash": admin_password_hash, "id": uid(1)})
    options = {"fail_audit": False}

    def test_db():
        with engine.connect() as connection:
            connection.exec_driver_sql("EXECUTE AS USER = 'task6_backend'").close()
            connection.exec_driver_sql(
                "EXEC sys.sp_set_session_context @key=N'task6_fail_audit', @value="
                + ("1" if options["fail_audit"] else "NULL")
            ).close()
            connection.commit()
            try:
                with Session(bind=connection) as session:
                    yield session
            finally:
                connection.rollback()
                connection.exec_driver_sql("REVERT").close()
                connection.commit()

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = test_db
    try:
        with TestClient(app) as client:
            yield client, engine, options
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


def headers(user: int = 1, *, expires: int = 60, secret: str = JWT_SECRET_KEY, **claims):
    payload = {"sub": uid(user), "exp": datetime.now(timezone.utc) + timedelta(seconds=expires), **claims}
    return {"Authorization": "Bearer " + jwt.encode(payload, secret, algorithm="HS256")}


def scalar(engine, sql: str, **params):
    with engine.connect() as connection:
        return connection.execute(text(sql), params).scalar()


ENDPOINTS = [
    ("GET", "/api/admin/configs", None),
    ("GET", "/api/admin/configs/site.name", None),
    ("POST", "/api/admin/configs", {"config_key": "site.name", "config_value": "FamilyConnect"}),
    ("PUT", "/api/admin/configs/site.name", {"config_value": "Updated"}),
    ("DELETE", "/api/admin/configs/site.name", None),
    ("GET", "/api/admin/verifications/pending", None),
    ("PATCH", f"/api/admin/verifications/{uid(4001)}/review", {"decision": "approved"}),
]


@pytest.mark.parametrize("method,path,body", ENDPOINTS)
def test_all_admin_endpoints_require_jwt(api, method, path, body):
    client, _, _ = api
    response = client.request(method, path, json=body)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("method,path,body", ENDPOINTS)
@pytest.mark.parametrize("user", [3, 4])
def test_member_and_guest_cannot_use_admin_api(api, method, path, body, user):
    assert api[0].request(method, path, json=body, headers=headers(user)).status_code == 403


@pytest.mark.parametrize("method,path,body", ENDPOINTS[:5])
def test_family_head_cannot_manage_system_configs(api, method, path, body):
    assert api[0].request(method, path, json=body, headers=headers(2)).status_code == 403


@pytest.mark.parametrize("auth", [headers(5), headers(999), headers(expires=-60), headers(secret="wrong-secret-at-least-32-characters"), {"Authorization": "Bearer invalid"}])
def test_inactive_unknown_expired_and_invalid_credentials(api, auth):
    assert api[0].get("/api/admin/configs", headers=auth).status_code == 401


def test_jwt_role_claim_cannot_elevate_member(api):
    assert api[0].get("/api/admin/configs", headers=headers(3, role="admin")).status_code == 403


def test_admin_login_and_config_crud_persist_with_backend_permissions(api):
    client, engine, _ = api
    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "Task6-Test-Admin!2026"})
    assert login.status_code == 200, login.text
    auth = {"Authorization": "Bearer " + login.json()["access_token"]}
    payload = {"config_key": "site.name", "config_value": "Gia phả Việt Nam — ' ; DROP TABLE core.Users; --", "description": "Tên ứng dụng"}
    created = client.post("/api/admin/configs", json=payload, headers=auth)
    assert created.status_code == 201, created.text
    assert created.json()["config_value"] == payload["config_value"]
    assert "ConfigKey" not in created.json()
    assert client.get("/api/admin/configs/site.name", headers=auth).json() == created.json()
    assert len(client.get("/api/admin/configs", headers=auth).json()) == 1
    with engine.begin() as connection:
        connection.exec_driver_sql("UPDATE core.SystemConfigs SET UpdatedAt='20000101'").close()
        # The real trigger overwrites even an explicit old timestamp.
    updated = client.put("/api/admin/configs/site.name", json={"config_value": "Mới"}, headers=auth)
    assert updated.status_code == 200, updated.text
    assert updated.json()["description"] is None
    assert datetime.fromisoformat(updated.json()["updated_at"]).year >= 2026
    assert scalar(engine, "SELECT ConfigValue FROM core.SystemConfigs WHERE ConfigKey='site.name'") == "Mới"
    deleted = client.delete("/api/admin/configs/site.name", headers=auth)
    assert deleted.status_code == 204 and deleted.content == b""
    assert client.get("/api/admin/configs/site.name", headers=auth).status_code == 404
    assert scalar(engine, "SELECT COUNT(*) FROM reports.AuditLog WHERE UserId=:id AND Action LIKE 'system_config.%'", id=uid(1)) == 3


def test_duplicate_key_returns_conflict_and_preserves_original(api):
    client, engine, _ = api
    assert client.post("/api/admin/configs", json={"config_key": "site.name", "config_value": "old"}, headers=headers()).status_code == 201
    response = client.post("/api/admin/configs", json={"config_key": "SITE.NAME", "config_value": "overwrite"}, headers=headers())
    assert response.status_code == 409, response.text
    assert scalar(engine, "SELECT ConfigValue FROM core.SystemConfigs WHERE ConfigKey='site.name'") == "old"
    assert scalar(engine, "SELECT COUNT(*) FROM reports.AuditLog") == 1


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
def test_missing_config_returns_not_found(api, method):
    response = api[0].request(method, "/api/admin/configs/missing", headers=headers(),
                              json={"config_value": "new"} if method == "PUT" else None)
    assert response.status_code == 404, response.text


@pytest.mark.parametrize("payload", [
    {"config_key": "", "config_value": "x"},
    {"config_key": "x" * 101, "config_value": "x"},
    {"config_key": "khóa", "config_value": "x"},
    {"config_key": "x", "config_value": None},
    {"config_key": "x", "config_value": "x", "description": "x" * 501},
    {"config_key": "x", "config_value": "x", "actor_id": uid(2)},
])
def test_config_validation(api, payload):
    assert api[0].post("/api/admin/configs", json=payload, headers=headers()).status_code == 422


@pytest.mark.parametrize("query", ["limit=0", "limit=201", "offset=-1", "offset=2147483648"])
@pytest.mark.parametrize("path", ["configs", "verifications/pending"])
def test_pagination_validation(api, query, path):
    assert api[0].get(f"/api/admin/{path}?{query}", headers=headers()).status_code == 422


@pytest.mark.parametrize("user,expected", [(1, set(range(4001, 4011))), (2, {4001, 4002, 4010}), (6, {4004}), (7, set()), (11, {4003, 4006})])
def test_pending_verifications_respect_family_and_branch_scope(api, user, expected):
    response = api[0].get("/api/admin/verifications/pending", headers=headers(user))
    assert response.status_code == 200, response.text
    assert {UUID(row["verification_id"]).int for row in response.json()} == expected
    assert all("password_hash" not in row for row in response.json())


def test_pending_pagination_is_stable(api):
    client, _, _ = api
    first = client.get("/api/admin/verifications/pending?limit=2", headers=headers()).json()
    second = client.get("/api/admin/verifications/pending?limit=2&offset=2", headers=headers()).json()
    assert len(first) == len(second) == 2
    assert {row["verification_id"] for row in first}.isdisjoint(row["verification_id"] for row in second)


def test_approval_links_member_rejects_competitors_and_commits(api):
    client, engine, _ = api
    response = client.patch(f"/api/admin/verifications/{uid(4001)}/review", json={"decision": "approved"}, headers=headers(2))
    assert response.status_code == 200, response.text
    assert response.json() == {"verification_id": uid(4001), "status": "approved", "auto_rejected_count": 2}
    assert str(scalar(engine, "SELECT UserId FROM genealogy.Members WHERE Id=:id", id=uid(3001))).lower() == uid(3)
    assert scalar(engine, "SELECT COUNT(*) FROM core.MemberVerifications WHERE Id IN (:a,:b) AND Status='rejected'", a=uid(4002), b=uid(4003)) == 2
    assert scalar(engine, "SELECT COUNT(*) FROM reports.AuditLog WHERE UserId=:id AND Action LIKE 'verification.approved%'", id=uid(2)) == 1
    assert client.patch(f"/api/admin/verifications/{uid(4001)}/review", json={"decision": "approved"}, headers=headers()).status_code == 409


def test_rejection_does_not_link_member_or_reject_competitors(api):
    client, engine, _ = api
    response = client.patch(f"/api/admin/verifications/{uid(4001)}/review", json={"decision": "rejected"}, headers=headers(2))
    assert response.status_code == 200, response.text
    assert response.json()["auto_rejected_count"] == 0
    assert scalar(engine, "SELECT UserId FROM genealogy.Members WHERE Id=:id", id=uid(3001)) is None
    assert scalar(engine, "SELECT Status FROM core.MemberVerifications WHERE Id=:id", id=uid(4002)) == "pending"


@pytest.mark.parametrize("request_id", [4003, 4004, 4005, 4007])
def test_head_cannot_review_other_branch_family_unassigned_or_self(api, request_id):
    response = api[0].patch(f"/api/admin/verifications/{uid(request_id)}/review", json={"decision": "approved"}, headers=headers(2))
    assert response.status_code == 403, response.text


@pytest.mark.parametrize("request_id,code", [(9999, 404), (4008, 409), (4009, 409), (4010, 409)])
def test_review_database_errors_become_http_errors(api, request_id, code):
    response = api[0].patch(f"/api/admin/verifications/{uid(request_id)}/review", json={"decision": "approved"}, headers=headers())
    assert response.status_code == code, response.text


@pytest.mark.parametrize("payload", [{"decision": "pending"}, {"decision": "approved", "reviewer_id": uid(1)}])
def test_invalid_review_and_forged_actor_are_rejected(api, payload):
    assert api[0].patch(f"/api/admin/verifications/{uid(4001)}/review", json=payload, headers=headers(2)).status_code == 422


@pytest.mark.parametrize("action", ["create", "update", "delete", "review"])
def test_failed_audit_rolls_back_the_entire_operation(api, action):
    client, engine, options = api
    if action in {"update", "delete"}:
        assert client.post("/api/admin/configs", json={"config_key": "site.name", "config_value": "old"}, headers=headers()).status_code == 201
    options["fail_audit"] = True
    if action == "create":
        response = client.post("/api/admin/configs", json={"config_key": "site.name", "config_value": "new"}, headers=headers())
    elif action == "update":
        response = client.put("/api/admin/configs/site.name", json={"config_value": "new"}, headers=headers())
    elif action == "delete":
        response = client.delete("/api/admin/configs/site.name", headers=headers())
    else:
        response = client.patch(f"/api/admin/verifications/{uid(4001)}/review", json={"decision": "approved"}, headers=headers())
    assert response.status_code == 500, response.text
    assert response.json() == {"detail": "Không thể xử lý yêu cầu quản trị."}
    if action in {"update", "delete"}:
        assert scalar(engine, "SELECT ConfigValue FROM core.SystemConfigs WHERE ConfigKey='site.name'") == "old"
        assert scalar(engine, "SELECT COUNT(*) FROM reports.AuditLog") == 1
    else:
        assert scalar(engine, "SELECT COUNT(*) FROM core.SystemConfigs") == 0
        assert scalar(engine, "SELECT COUNT(*) FROM reports.AuditLog") == 0
        assert scalar(engine, "SELECT Status FROM core.MemberVerifications WHERE Id=:id", id=uid(4001)) == "pending"
        assert scalar(engine, "SELECT Status FROM core.MemberVerifications WHERE Id=:id", id=uid(4002)) == "pending"
        assert scalar(engine, "SELECT UserId FROM genealogy.Members WHERE Id=:id", id=uid(3001)) is None
