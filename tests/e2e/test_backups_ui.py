"""Browser checks with mocked APIs; never restores the developer's database."""
from urllib.parse import urlparse
import time

import pytest
from playwright.sync_api import expect

from test_admin_pages import open_as, SITE_DEFAULTS

IDENTIFIER = "00000000-0000-0000-0000-000000007001"
ROW = {"id": IDENTIFIER, "file_name": f"fc_{IDENTIFIER}.bak", "created_at": "2026-11-22T13:41:44Z", "size_bytes": 1048576}


@pytest.fixture(scope="module")
def backup_app(e2e_browser, vite_server):
    with vite_server() as url:
        yield e2e_browser, url


@pytest.fixture
def backup_ui(backup_app):
    browser, url = backup_app
    context = browser.new_context(base_url=url, viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    page.set_default_navigation_timeout(30000)
    state = {"rows": [], "calls": [], "error": None, "delete_error": None, "hold": False, "held": []}

    def respond(route):
        request = route.request
        path = urlparse(request.url).path
        if not path.startswith("/api/"): route.continue_(); return
        if path == "/api/settings": route.fulfill(json=SITE_DEFAULTS); return
        if path == "/api/admin/backups":
            if request.method == "GET":
                route.fulfill(json={"database": "OwnedTestDatabase", "backups": state["rows"]})
            else:
                state["calls"].append((path, request.post_data_json))
                if state["hold"]: state["held"].append(route); return
                state["rows"] = [ROW]
                route.fulfill(status=201, json=ROW)
            return
        if request.method == "DELETE" and path.startswith("/api/admin/backups/"):
            state["calls"].append((path, None))
            if state["hold"]: state["held"].append(route); return
            if state["delete_error"]:
                route.fulfill(status=503, json={"detail": "Không xóa được file sao lưu."}); return
            state["rows"] = [row for row in state["rows"] if row["id"] != path.rsplit("/", 1)[1]]
            route.fulfill(status=204)
            return
        if path.endswith("/restore"):
            state["calls"].append((path, request.post_data_json))
            if state["error"]: route.fulfill(status=403, json={"detail": "Mật khẩu quản trị không đúng."}); return
            route.fulfill(json={"database": "OwnedTestDatabase", "safety_backup_id": IDENTIFIER, "message": "Đã khôi phục database. Hãy đăng nhập lại."})
            return
        route.fulfill(json={"unread_count": 0, "items": [], "total": 0} if path.startswith("/api/notifications") else [])

    page.route("**/api/**", respond)
    try:
        yield page, state
    finally:
        context.close()


def test_backup_create_and_prevent_duplicate(backup_ui):
    page, state = backup_ui
    open_as(page, "/admin-backups")
    expect(page.get_by_text("Chưa có bản sao lưu.", exact=False)).to_be_visible()
    state["hold"] = True
    button = page.get_by_role("button", name="Tạo bản sao lưu", exact=True)
    button.click()
    expect(button).to_be_disabled()
    expect(page.get_by_text("Đang sao lưu và kiểm tra file…", exact=False)).to_be_visible()
    deadline = time.monotonic() + 10
    while not state["held"] and time.monotonic() < deadline:
        page.wait_for_timeout(10)
    assert len(state["calls"]) == 1
    state["rows"] = [ROW]
    state["held"].pop().fulfill(status=201, json=ROW)
    expect(page.get_by_role("row").filter(has_text=ROW["file_name"])).to_be_visible()


@pytest.mark.parametrize("browser_timezone,timestamp,hour,date", [
    ("UTC", "2026-11-22T13:41:44Z", "20:41:44", "22/11/2026"),
    ("America/New_York", "2026-11-22T13:41:44Z", "20:41:44", "22/11/2026"),
    ("Asia/Ho_Chi_Minh", "2026-11-22T20:41:44+07:00", "20:41:44", "22/11/2026"),
    ("UTC", "2026-11-22T20:41:44Z", "03:41:44", "23/11/2026"),
])
def test_backup_time_uses_vietnam_timezone(backup_app, browser_timezone, timestamp, hour, date):
    browser, url = backup_app
    context = browser.new_context(base_url=url, timezone_id=browser_timezone)
    page = context.new_page()
    page.set_default_navigation_timeout(30000)
    def respond(route):
        path = urlparse(route.request.url).path
        if path == "/api/settings": route.fulfill(json=SITE_DEFAULTS)
        elif path == "/api/admin/backups": route.fulfill(json={"database": "OwnedTestDatabase", "backups": [{**ROW, "created_at": timestamp}]})
        else: route.continue_()
    page.route("**/api/**", respond)
    try:
        open_as(page, "/admin-backups")
        row = page.get_by_role("row").filter(has_text=ROW["file_name"])
        expect(row).to_contain_text(hour)
        expect(row).to_contain_text(date)
    finally:
        context.close()


def test_restore_confirmation_error_and_success(backup_ui):
    page, state = backup_ui
    state["rows"] = [ROW]
    open_as(page, "/admin-backups")
    page.get_by_role("button", name=f"Khôi phục {ROW['file_name']}", exact=True).click()
    confirm = page.get_by_role("button", name="Xác nhận ghi đè và khôi phục")
    expect(confirm).to_be_disabled()
    page.get_by_label("Nhập tên database:", exact=False).fill("wrong")
    page.get_by_label("Mật khẩu admin hiện tại").fill("wrong-password")
    expect(confirm).to_be_disabled()
    assert state["calls"] == []
    page.get_by_label("Nhập tên database:", exact=False).fill("OwnedTestDatabase")
    state["error"] = True
    confirm.click()
    expect(page.get_by_role("alert")).to_have_text("Mật khẩu quản trị không đúng.")
    expect(page.get_by_label("Mật khẩu admin hiện tại")).to_have_value("")
    assert page.evaluate("Boolean(localStorage.getItem('familyconnect.token'))")
    state["error"] = None
    page.get_by_label("Mật khẩu admin hiện tại").fill("correct-password")
    confirm.click()
    expect(page).to_have_url("/login")
    expect(page.get_by_role("status").filter(has_text="Đã khôi phục database.")).to_be_visible()
    assert page.evaluate("localStorage.getItem('familyconnect.token')") is None


def test_delete_confirmation_and_clear_selected_restore(backup_ui):
    page, state = backup_ui
    state["rows"] = [ROW]
    open_as(page, "/admin-backups")
    page.get_by_role("button", name=f"Khôi phục {ROW['file_name']}", exact=True).click()
    delete = page.get_by_role("button", name=f"Xóa {ROW['file_name']}", exact=True)
    page.once("dialog", lambda dialog: dialog.dismiss())
    delete.click()
    assert state["calls"] == []
    expect(page.get_by_role("row").filter(has_text=ROW["file_name"])).to_be_visible()
    page.once("dialog", lambda dialog: dialog.accept())
    delete.click()
    expect(page.get_by_text("Chưa có bản sao lưu.", exact=False)).to_be_visible()
    expect(page.get_by_role("heading", name="Xác nhận khôi phục", exact=True)).to_have_count(0)
    assert state["calls"] == [(f"/api/admin/backups/{IDENTIFIER}", None)]


def test_delete_failure_keeps_row(backup_ui):
    page, state = backup_ui
    state["rows"], state["delete_error"] = [ROW], True
    open_as(page, "/admin-backups")
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name=f"Xóa {ROW['file_name']}", exact=True).click()
    expect(page.get_by_role("alert")).to_have_text("Không xóa được file sao lưu.")
    expect(page.get_by_role("row").filter(has_text=ROW["file_name"])).to_be_visible()


def test_delete_disables_operations_while_pending(backup_ui):
    page, state = backup_ui
    state["rows"], state["hold"] = [ROW], True
    open_as(page, "/admin-backups")
    page.once("dialog", lambda dialog: dialog.accept())
    delete = page.get_by_role("button", name=f"Xóa {ROW['file_name']}", exact=True)
    delete.click()
    expect(delete).to_be_disabled()
    expect(page.get_by_role("button", name="Tạo bản sao lưu", exact=True)).to_be_disabled()
    expect(page.get_by_role("button", name=f"Khôi phục {ROW['file_name']}", exact=True)).to_be_disabled()
    deadline = time.monotonic() + 10
    while not state["held"] and time.monotonic() < deadline:
        page.wait_for_timeout(10)
    assert len(state["calls"]) == 1
    state["rows"] = []
    state["held"].pop().fulfill(status=204)
    expect(page.get_by_text("Chưa có bản sao lưu.", exact=False)).to_be_visible()


@pytest.mark.parametrize("role", ["member", "family_head", "guest"])
def test_backup_page_hidden_for_other_roles(backup_ui, role):
    page, state = backup_ui
    open_as(page, "/admin-backups", role=role)
    expect(page.get_by_role("heading", name="Sao lưu & khôi phục", exact=True)).to_have_count(0)
    expect(page.get_by_role("link", name="Sao lưu & khôi phục", exact=True)).to_have_count(0)
    assert state["calls"] == []


def test_backup_small_screen(backup_ui):
    page, state = backup_ui
    state["rows"] = [ROW]
    page.set_viewport_size({"width": 390, "height": 844})
    open_as(page, "/admin-backups")
    expect(page.get_by_role("heading", name="Sao lưu & khôi phục", exact=True)).to_be_visible()
    page.get_by_role("button", name=f"Khôi phục {ROW['file_name']}", exact=True).click()
    expect(page.get_by_label("Mật khẩu admin hiện tại")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
