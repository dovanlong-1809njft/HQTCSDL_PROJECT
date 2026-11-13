"""Task 9: browser -> Vite proxy -> FastAPI -> isolated SQL Server, real auth/JWT."""
import json
import os
from pathlib import Path
import re
import socket
import sys
from threading import Thread
import time

import pytest

if os.getenv("RUN_TASK9_E2E") != "1":
    pytest.skip("Set RUN_TASK9_E2E=1 for real login E2E.", allow_module_level=True)

from sqlalchemy import text
from sqlalchemy.orm import Session
import uvicorn

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "api"))
from test_admin import execute_script, hash_password, sql_database, uid  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.main import app  # noqa: E402

playwright = pytest.importorskip("playwright.sync_api")
expect = playwright.expect
PASSWORD = "Task9-Test-Password!2026"


@pytest.fixture(scope="session")
def login_app(sql_database, vite_server):
    engine, _ = sql_database

    def test_db():
        with engine.connect() as connection:
            connection.exec_driver_sql("EXECUTE AS USER = 'task6_backend'").close()
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
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning",
                                              access_log=False, lifespan="off", timeout_graceful_shutdown=5))
        thread = Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
        try:
            thread.start()
            deadline = time.monotonic() + 30
            while not server.started:
                if not thread.is_alive() or time.monotonic() > deadline:
                    pytest.fail("The isolated FastAPI server did not start.")
                time.sleep(0.05)
            with vite_server(f"http://127.0.0.1:{port}") as url:
                yield url
        finally:
            server.should_exit = True
            if thread.ident is not None:
                thread.join(timeout=10)
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous)
            assert not thread.is_alive(), "The isolated FastAPI server did not stop."


@pytest.fixture(scope="session")
def login_password_hash():
    return hash_password(PASSWORD)


@pytest.fixture
def login_ui(e2e_browser, login_app, sql_database, login_password_hash):
    engine, name = sql_database
    with engine.begin() as connection:
        for path in ("tests/database/task6.integration.sql", "tests/database/task9.integration.sql"):
            execute_script(connection, (ROOT / path).read_text(encoding="utf-8-sig"), name)
        connection.execute(text("UPDATE core.Users SET PasswordHash = :hash"), {"hash": login_password_hash})
    context = e2e_browser.new_context(base_url=login_app, viewport={"width": 1440, "height": 1000})
    errors, requests = [], []
    context.on("page", lambda page: page.on("pageerror", lambda error: errors.append(str(error))))
    context.on("request", lambda request: requests.append(request) if "/api/" in request.url else None)
    page = context.new_page()
    page.set_default_timeout(10000)
    try:
        yield page, engine, requests
        assert not errors, errors
    finally:
        context.close()


def submit_login(page, email="admin@example.com", password=PASSWORD):
    page.get_by_label("Email", exact=True).fill(email)
    page.get_by_label("Mật khẩu", exact=True).fill(password)
    page.get_by_role("button", name="Đăng nhập", exact=True).click()


def current_session(page):
    token = page.evaluate("localStorage.getItem('familyconnect.token')")
    assert token and not token.startswith("demo-token-")
    profile = page.request.get("/api/auth/me", headers={"Authorization": "Bearer " + token})
    assert profile.status == 200, profile.text()
    user = profile.json()
    assert "password_hash" not in user
    assert json.loads(page.evaluate("localStorage.getItem('familyconnect.user')"))["role"] == user["role"]
    return user


@pytest.mark.parametrize("email,role,path,destination,title", [
    ("ADMIN@EXAMPLE.COM", "admin", "/admin-config", "/admin-config", "Cấu hình hệ thống"),
    ("head@example.com", "family_head", "/member-approval", "/member-approval", "Duyệt thành viên"),
    ("member@example.com", "member", "/reports", "/dashboard", "Không gian gia đình"),
    ("guest@example.com", "guest", "/admin-config", "/dashboard", "Không gian gia đình"),
])
def test_login_returns_to_allowed_destination(login_ui, email, role, path, destination, title):
    page, _, requests = login_ui
    page.goto(path)
    expect(page).to_have_url(re.compile(r"/login$"))
    with page.expect_response("**/api/auth/login") as login:
        submit_login(page, email)
    assert login.value.status == 200
    expect(page).to_have_url(re.compile(re.escape(destination) + "$"))
    expect(page.get_by_role("heading", name=title, exact=True)).to_be_visible()
    assert current_session(page)["role"] == role
    if role in {"member", "guest"}:
        assert not any("/api/admin/" in request.url for request in requests)
        expect(page.get_by_role("link", name="Cấu hình hệ thống", exact=True)).to_have_count(0)


@pytest.mark.parametrize("email,password", [
    ("admin@example.com", "Wrong-Password!2026"),
    ("missing@example.com", PASSWORD),
    ("inactive@example.com", PASSWORD),
])
def test_invalid_credentials_and_locked_account_cannot_login(login_ui, email, password):
    page, _, _ = login_ui
    page.goto("/login")
    with page.expect_response("**/api/auth/login") as login:
        submit_login(page, email, password)
    assert login.value.status == 401
    expect(page.get_by_role("alert")).to_contain_text("Đăng nhập chưa thành công")
    expect(page).to_have_url(re.compile(r"/login$"))
    expect(page.get_by_label("Email", exact=True)).to_have_value(email)
    assert page.evaluate("localStorage.getItem('familyconnect.token')") is None


def test_login_validation_blocks_requests(login_ui):
    page, _, requests = login_ui
    page.goto("/login")
    submit_login(page, "invalid-email", "123")
    expect(page.get_by_text("Email chưa đúng định dạng.", exact=True)).to_be_visible()
    expect(page.get_by_text("Mật khẩu cần có ít nhất 6 ký tự.", exact=True)).to_be_visible()
    assert not any(request.url.endswith("/api/auth/login") for request in requests)


def test_register_logout_and_login_persists_real_account(login_ui):
    page, engine, _ = login_ui
    page.goto("/register")
    page.get_by_label("Họ và tên", exact=True).fill("Nguyễn Ánh — Task 9")
    page.get_by_label("Email", exact=True).fill("task9.new@example.com")
    page.get_by_label("Mật khẩu", exact=True).fill(PASSWORD)
    page.get_by_label("Nhập lại mật khẩu", exact=True).fill(PASSWORD)
    with page.expect_response("**/api/auth/register") as registered:
        page.get_by_role("button", name="Đăng ký", exact=True).click()
    assert registered.value.status == 201
    expect(page).to_have_url(re.compile(r"/dashboard$"))
    user = current_session(page)
    assert user["role"] == "member" and user["full_name"] == "Nguyễn Ánh — Task 9"
    with engine.connect() as connection:
        stored = connection.execute(text("SELECT PasswordHash FROM core.Users WHERE Email=:email"),
                                    {"email": "task9.new@example.com"}).scalar_one()
    assert stored != PASSWORD and stored.startswith("$argon2")
    page.get_by_role("button", name="Đăng xuất", exact=True).click()
    expect(page).to_have_url(re.compile(r"/login$"))
    submit_login(page, "task9.new@example.com")
    expect(page).to_have_url(re.compile(r"/dashboard$"))
    assert current_session(page)["id"] == user["id"]


def test_duplicate_registration_shows_conflict(login_ui):
    page, _, _ = login_ui
    page.goto("/register")
    page.get_by_label("Họ và tên", exact=True).fill("Task 9 duplicate")
    page.get_by_label("Email", exact=True).fill("admin@example.com")
    page.get_by_label("Mật khẩu", exact=True).fill(PASSWORD)
    page.get_by_label("Nhập lại mật khẩu", exact=True).fill(PASSWORD)
    with page.expect_response("**/api/auth/register") as registered:
        page.get_by_role("button", name="Đăng ký", exact=True).click()
    assert registered.value.status == 409
    expect(page.get_by_role("alert")).to_contain_text("Email này đã được đăng ký")
    assert page.evaluate("localStorage.getItem('familyconnect.token')") is None


def test_registration_password_confirmation_blocks_requests(login_ui):
    page, _, requests = login_ui
    page.goto("/register")
    page.get_by_label("Họ và tên", exact=True).fill("Task 9 mismatch")
    page.get_by_label("Email", exact=True).fill("task9.new@example.com")
    page.get_by_label("Mật khẩu", exact=True).fill(PASSWORD)
    page.get_by_label("Nhập lại mật khẩu", exact=True).fill("Different-password!2026")
    page.get_by_role("button", name="Đăng ký", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("Hai mật khẩu chưa trùng nhau")
    assert not any(request.url.endswith("/api/auth/register") for request in requests)


def test_reload_cross_tab_logout_and_account_switch(login_ui):
    page, _, _ = login_ui
    page.goto("/admin-config")
    submit_login(page)
    expect(page.get_by_text("TASK9 private configuration", exact=True)).to_be_visible()
    page.reload()
    expect(page.get_by_text("TASK9 private configuration", exact=True)).to_be_visible()
    other = page.context.new_page()
    other.goto("/admin-config")
    expect(other.get_by_text("TASK9 private configuration", exact=True)).to_be_visible()
    page.get_by_role("button", name="Đăng xuất", exact=True).click()
    expect(page).to_have_url(re.compile(r"/login$"))
    expect(other).to_have_url(re.compile(r"/login$"))
    assert page.evaluate("localStorage.getItem('familyconnect.token')") is None
    submit_login(page, "member@example.com")
    expect(page).to_have_url(re.compile(r"/dashboard$"))
    expect(other).to_have_url(re.compile(r"/dashboard$"))
    expect(other.get_by_text("TASK9 private configuration", exact=True)).to_have_count(0)
    assert current_session(page)["role"] == "member"
    assert current_session(other)["role"] == "member"


def test_expired_real_jwt_redirects_to_login(login_ui, monkeypatch):
    page, _, _ = login_ui
    monkeypatch.setattr("app.core.security.ACCESS_TOKEN_MINUTES", -1)
    page.goto("/login")
    with page.expect_response("**/api/admin/statistics") as denied:
        submit_login(page)
    assert denied.value.status == 401
    expect(page).to_have_url(re.compile(r"/login$"))
    assert page.evaluate("localStorage.getItem('familyconnect.token')") is None


def test_account_locked_after_login_invalidates_session(login_ui):
    page, engine, _ = login_ui
    page.goto("/admin-config")
    submit_login(page)
    expect(page.get_by_text("TASK9 private configuration", exact=True)).to_be_visible()
    with engine.begin() as connection:
        connection.execute(text("UPDATE core.Users SET IsActive=0 WHERE UserId=:id"), {"id": uid(1)})
    with page.expect_response("**/api/admin/configs?*") as denied:
        page.get_by_role("button", name="Làm mới", exact=True).click()
    assert denied.value.status == 401
    expect(page).to_have_url(re.compile(r"/login$"))
    assert page.evaluate("localStorage.getItem('familyconnect.token')") is None


def test_backend_enforces_role_change_after_login(login_ui):
    page, engine, _ = login_ui
    page.goto("/admin-config")
    submit_login(page)
    expect(page.get_by_text("TASK9 private configuration", exact=True)).to_be_visible()
    with engine.begin() as connection:
        connection.execute(text("UPDATE core.Users SET Role='member' WHERE UserId=:id"), {"id": uid(1)})
    with page.expect_response("**/api/admin/configs?*") as denied:
        page.get_by_role("button", name="Làm mới", exact=True).click()
    assert denied.value.status == 403
    expect(page.get_by_role("alert")).to_contain_text("Bạn không có quyền")
    expect(page.get_by_text("TASK9 private configuration", exact=True)).to_have_count(0)


def test_network_error_cannot_fall_back_to_demo_login(login_ui):
    page, _, _ = login_ui
    page.goto("/login")
    page.route("**/api/auth/login", lambda route: route.abort("connectionrefused"))
    submit_login(page)
    expect(page.get_by_role("alert")).to_contain_text("Đăng nhập chưa thành công")
    expect(page).to_have_url(re.compile(r"/login$"))
    assert page.evaluate("localStorage.getItem('familyconnect.token')") is None
