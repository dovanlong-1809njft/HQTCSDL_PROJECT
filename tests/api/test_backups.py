"""Backup API boundaries and native restore on an owned, disposable SQL database."""
from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from test_admin import sql_database, admin_password_hash, headers, uid
from app.core.database import get_db
from app.core.maintenance import application_lock
from app.domains.admin import backups
from app.domains.identity.models import User
from app.main import app

BACKUP_ID = UUID(int=7001)
ROW = dict(id=str(BACKUP_ID), file_name=f"fc_{BACKUP_ID}.bak", created_at=datetime(2026, 11, 22, tzinfo=timezone.utc), size_bytes=1048576)


@pytest.fixture
def backup_api(admin_password_hash):
    class Database:
        info = {}
        role = "admin"
        closed = False

        def scalar(self, statement):
            return User(id=UUID(int=1), role=self.role, is_active=True, email="backup@example.invalid",
                        full_name="Backup admin", password_hash=admin_password_hash)

        def close(self): self.closed = True

    class Backups:
        database = "OwnedTestDatabase"
        calls = []

        def list(self): return {"database": self.database, "backups": [ROW]}
        def create(self, actor): self.calls.append(("create", actor)); return ROW
        def delete(self, identifier, actor): self.calls.append(("delete", identifier, actor))
        def restore(self, identifier, actor):
            assert db.closed
            self.calls.append(("restore", identifier, actor))
            return {"database": self.database, "safety_backup_id": str(BACKUP_ID), "message": "Restored"}

    db, service = Database(), Backups()
    db.info = {}
    service.calls = []
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[backups.get_database_backups] = lambda: service
    try:
        with TestClient(app) as client:
            yield client, db, service
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


@pytest.mark.parametrize("method,path", [("GET", "/api/admin/backups"), ("POST", "/api/admin/backups"),
    ("DELETE", f"/api/admin/backups/{BACKUP_ID}"),
    ("POST", f"/api/admin/backups/{BACKUP_ID}/restore")])
@pytest.mark.parametrize("role", [None, "member", "family_head", "guest"])
def test_backup_requires_admin(backup_api, method, path, role):
    client, db, service = backup_api
    db.role = role or "admin"
    response = client.request(method, path, headers=headers() if role else {},
                              json={"database": service.database, "password": "Task6-Test-Admin!2026"})
    assert response.status_code == (403 if role else 401)
    assert service.calls == []


def test_backup_list_and_create(backup_api):
    client, _, service = backup_api
    response = client.get("/api/admin/backups", headers=headers())
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert "path" not in response.json()["backups"][0]
    assert response.json()["backups"][0]["created_at"].endswith("Z")
    assert client.post("/api/admin/backups", headers=headers()).status_code == 201
    assert service.calls == [("create", UUID(int=1))]


def test_backup_delete_and_invalid_identifier(backup_api):
    client, _, service = backup_api
    response = client.delete(f"/api/admin/backups/{BACKUP_ID}", headers=headers())
    assert response.status_code == 204 and not response.content
    assert service.calls == [("delete", BACKUP_ID, UUID(int=1))]
    response = client.delete("/api/admin/backups/not-a-uuid", headers=headers())
    assert response.status_code == 422
    assert len(service.calls) == 1


def test_delete_rejects_backup_outside_owned_directory(monkeypatch):
    manager = backups.DatabaseBackups(backups.engine)
    @contextmanager
    def connection(): yield object()
    monkeypatch.setattr(manager, "connection", connection)
    monkeypatch.setattr(backups, "application_lock", lambda *a, **k: nullcontext())
    monkeypatch.setattr(manager, "_check_admin", lambda *a: None)
    monkeypatch.setattr(manager, "_directory", lambda *a: "/var/opt/mssql/data/")
    monkeypatch.setattr(manager, "_catalog", lambda *a: [{"name": f"FamilyConnect:{BACKUP_ID}", "path": "/tmp/other.bak"}])
    calls = []
    monkeypatch.setattr(backups, "command", lambda *a: calls.append(a))
    with pytest.raises(HTTPException) as error:
        manager.delete(BACKUP_ID, UUID(int=1))
    assert error.value.status_code == 404 and not calls


@pytest.mark.parametrize("file_exists,audit_fails", [(1, False), (0, True)])
def test_delete_reports_file_or_audit_failure(monkeypatch, file_exists, audit_fails):
    manager = backups.DatabaseBackups(backups.engine)
    class Connection:
        def execute(self, *args, **kwargs): return self
        def scalar_one(self): return file_exists
    @contextmanager
    def connection(): yield Connection()
    monkeypatch.setattr(manager, "connection", connection)
    monkeypatch.setattr(backups, "application_lock", lambda *a, **k: nullcontext())
    monkeypatch.setattr(manager, "_check_admin", lambda *a: None)
    monkeypatch.setattr(manager, "_find", lambda *a: {"path": f"/var/opt/mssql/data/fc_{BACKUP_ID}.bak"})
    monkeypatch.setattr(backups, "command", lambda *a: None)
    audit_calls = []
    def audit(*args):
        audit_calls.append(args)
        if audit_fails: raise SQLAlchemyError("private SQL details")
    monkeypatch.setattr(manager, "_audit", audit)
    with pytest.raises(HTTPException) as error:
        manager.delete(BACKUP_ID, UUID(int=1))
    assert error.value.status_code == 503
    assert bool(audit_calls) == (not file_exists)
    assert "private SQL details" not in error.value.detail


@pytest.mark.parametrize("changes,code", [({"database": "wrong"}, 422), ({"password": "wrong"}, 403),
    ({"password": ""}, 422), ({"path": "../../other.bak"}, 422)])
def test_restore_confirmation_does_not_touch_database(backup_api, changes, code):
    client, db, service = backup_api
    body = {"database": service.database, "password": "Task6-Test-Admin!2026", **changes}
    response = client.post(f"/api/admin/backups/{BACKUP_ID}/restore", json=body, headers=headers())
    assert response.status_code == code
    assert not db.closed and not service.calls
    assert body["password"] not in response.text if body["password"] else True


def test_restore_releases_auth_connection_and_lock(backup_api):
    client, db, service = backup_api
    released = []
    db.info["release_database_access"] = lambda: released.append(True)
    response = client.post(f"/api/admin/backups/{BACKUP_ID}/restore", headers=headers(),
                           json={"database": service.database, "password": "Task6-Test-Admin!2026"})
    assert response.status_code == 200
    assert released == [True]
    assert service.calls == [("restore", BACKUP_ID, UUID(int=1))]


def test_restore_failure_recovers_safety_copy(monkeypatch):
    manager = backups.DatabaseBackups(backups.engine)
    selected, safety = {"id": "selected"}, {"id": "safety", "file_name": "safety.bak"}
    calls = []
    @contextmanager
    def connection(): yield object()
    monkeypatch.setattr(manager, "connection", connection)
    monkeypatch.setattr(backups, "application_lock", lambda *a, **k: nullcontext())
    monkeypatch.setattr(manager, "_check_admin", lambda *a: None)
    monkeypatch.setattr(manager, "_find", lambda *a: selected)
    monkeypatch.setattr(manager, "_verify", lambda *a: None)
    monkeypatch.setattr(manager, "_create", lambda *a: safety)
    monkeypatch.setattr(manager, "_audit", lambda *a: None)
    monkeypatch.setattr(manager.target_engine, "dispose", lambda: None)
    def restore(connection, row):
        calls.append(row["id"])
        if row is selected: raise SQLAlchemyError("test failure")
    monkeypatch.setattr(manager, "_restore", restore)
    with pytest.raises(HTTPException) as error:
        manager.restore(BACKUP_ID, UUID(int=1))
    assert error.value.status_code == 503
    assert calls == ["selected", "safety"]


def test_native_backup_restore_and_maintenance(sql_database, admin_password_hash, monkeypatch):
    engine, name = sql_database
    assert name.startswith("FamilyConnect_Task6Test_")
    master = create_engine(engine.url.set(database="master"), isolation_level="AUTOCOMMIT", pool_pre_ping=True)
    monkeypatch.setattr(backups, "master_engine", master)
    manager = backups.DatabaseBackups(engine)
    previous = app.dependency_overrides.copy()
    def test_db():
        with master.connect() as gate:
            with application_lock(gate, f"FamilyConnect:maintenance:{name}", "Shared") as release:
                with Session(bind=engine) as db:
                    db.info["release_database_access"] = release
                    yield db
    app.dependency_overrides[get_db] = test_db
    app.dependency_overrides[backups.get_database_backups] = lambda: manager
    try:
        with engine.begin() as connection:
            connection.execute(text("""INSERT INTO core.Users (UserId, Email, PasswordHash, FullName, Role, IsActive)
                VALUES (:id, 'backup-test@example.invalid', :hash, 'Backup test', 'admin', 1)"""),
                {"id": uid(7701), "hash": admin_password_hash})
            connection.exec_driver_sql("CREATE TABLE dbo.BackupRestoreProbe (Value int NOT NULL); INSERT dbo.BackupRestoreProbe VALUES (1)").close()
        with TestClient(app) as client:
            response = client.post("/api/admin/backups", headers=headers(7701))
            assert response.status_code == 201, response.text
            original = response.json()
        assert original["size_bytes"] > 0
        assert original["created_at"].endswith("Z")
        assert original["id"] in [row["id"] for row in manager.list()["backups"]]
        with engine.begin() as connection:
            connection.exec_driver_sql("UPDATE dbo.BackupRestoreProbe SET Value=2").close()
            connection.execute(text("""INSERT INTO core.Users (UserId, Email, PasswordHash, FullName, Role, IsActive)
                VALUES (:id, 'new-backup-admin@example.invalid', :hash, 'New test admin', 'admin', 1)"""),
                {"id": uid(7702), "hash": admin_password_hash})
        with master.connect() as first, master.connect() as second:
            with application_lock(first, f"FamilyConnect:maintenance:{name}"):
                with pytest.raises(HTTPException) as blocked:
                    with application_lock(second, f"FamilyConnect:maintenance:{name}", "Shared"): pass
                assert blocked.value.status_code == 503
            with application_lock(second, f"FamilyConnect:maintenance:{name}", "Shared"): pass
        with TestClient(app) as client:
            response = client.post(f"/api/admin/backups/{original['id']}/restore", headers=headers(7702),
                                   json={"database": name, "password": "Task6-Test-Admin!2026"})
            assert response.status_code == 200, response.text
            result = response.json()
        assert result["safety_backup_id"] != original["id"]
        with engine.connect() as connection:
            assert connection.exec_driver_sql("SELECT Value FROM dbo.BackupRestoreProbe").scalar_one() == 1
            assert connection.exec_driver_sql("SELECT COUNT(*) FROM reports.AuditLog WHERE Action LIKE 'RESTORE_DATABASE%'").scalar_one() == 1
            assert connection.exec_driver_sql("SELECT COUNT(*) FROM reports.AuditLog WHERE Action LIKE 'RESTORE_DATABASE%' AND UserId IS NULL").scalar_one() == 1
        # The automatic safety copy really contains the data from immediately before restore.
        manager.restore(UUID(result["safety_backup_id"]), UUID(int=7701))
        with engine.connect() as connection:
            assert connection.exec_driver_sql("SELECT Value FROM dbo.BackupRestoreProbe").scalar_one() == 2
        with pytest.raises(HTTPException) as missing:
            manager.restore(UUID(int=999999), UUID(int=7701))
        assert missing.value.status_code == 404
        with master.connect() as connection:
            original_path = manager._find(connection, UUID(original["id"]))["path"]
            with application_lock(connection, f"FamilyConnect:operations:{name}"):
                with pytest.raises(HTTPException) as busy:
                    manager.delete(UUID(original["id"]), UUID(int=7701))
                assert busy.value.status_code == 503
        count = len(manager.list()["backups"])
        with TestClient(app) as client:
            response = client.delete(f"/api/admin/backups/{original['id']}", headers=headers(7701))
            assert response.status_code == 204, response.text
            assert client.delete(f"/api/admin/backups/{original['id']}", headers=headers(7701)).status_code == 404
        assert len(manager.list()["backups"]) == count - 1
        with master.connect() as connection:
            assert connection.execute(text("SELECT file_exists FROM sys.dm_os_file_exists(:path)"), {"path": original_path}).scalar_one() == 0
        with engine.connect() as connection:
            assert connection.exec_driver_sql("SELECT Value FROM dbo.BackupRestoreProbe").scalar_one() == 2
            assert connection.exec_driver_sql("SELECT COUNT(*) FROM reports.AuditLog WHERE Action LIKE 'DELETE_BACKUP%'").scalar_one() == 1
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        # Only clean up files created for this disposable test database.
        for row in manager.list()["backups"]:
            manager.delete(UUID(row["id"]), UUID(int=7701))
        with engine.begin() as connection:
            connection.exec_driver_sql("DROP TABLE IF EXISTS dbo.BackupRestoreProbe").close()
        master.dispose()
