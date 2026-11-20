"""Task 7/8 UI checks. Run with RUN_TASK7_UI=1; HTTP APIs are mocked, SQL is untouched."""
import os
import re
import time
from urllib.parse import parse_qs, unquote, urlparse

import pytest

playwright = pytest.importorskip("playwright.sync_api")
expect = playwright.expect
SITE_DEFAULTS = {"site_name": "FamilyConnect", "logo_url": "/favicon.svg", "theme": "forest", "registration_enabled": True}
SITE_KEYS = {"site.name": "site_name", "site.logo_url": "logo_url", "site.theme": "theme", "registration.enabled": "registration_enabled"}


@pytest.fixture(scope="session")
def browser_app(e2e_browser, vite_server):
    if os.getenv("RUN_TASK7_UI") != "1":
        pytest.skip("Set RUN_TASK7_UI=1 to run browser checks.")
    with vite_server() as url:
        yield e2e_browser, url


def pending(identifier, name, member, branch="Chi A", active=True):
    return {
        "verification_id": identifier, "user_id": name, "user_full_name": name,
        "user_email": f"{identifier}@example.com", "user_is_active": active,
        "member_id": member, "member_full_name": f"Hồ sơ {name}", "birth_date": "1990-01-02",
        "family_id": "family", "family_name": "Họ Nguyễn", "branch_id": branch,
        "branch_name": branch, "linked_user_id": None, "status": "pending",
        "requested_at": "2026-11-12T08:30:00",
    }


def reported(identifier, target="post-a"):
    return {
        "report_id": identifier, "target_id": target or "missing", "target_type": "post",
        "reporter_name": "Người báo cáo", "reason": "Nội dung không phù hợp", "status": "pending",
        "created_at": "2026-11-13T08:30:00", "family_name": "Họ Nguyễn",
        "target_content": "Bài viết cần kiểm duyệt" if target else None, "can_resolve": bool(target),
    }


@pytest.fixture
def ui(browser_app):
    browser, url = browser_app
    context = browser.new_context(base_url=url, viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    page.set_default_timeout(10000)
    page.set_default_navigation_timeout(30000)
    state = {"configs": {}, "pending": [pending("a", "Nguyễn An", "member-a"),
             pending("b", "Trần Bình", "member-a"), pending("c", "Lê Chi", "member-c", "Chi B")],
             "requests": [], "read_error": None, "write_error": None, "hold_write": False, "held": [],
             "statistics": [{"family_id": "family-a", "family_name": "Họ Nguyễn", "member_count": 6, "post_count": 2, "event_count": 3},
                            {"family_id": "family-b", "family_name": "Họ Trần", "member_count": 4, "post_count": 1, "event_count": 0}],
             "reports": [reported("r1"), reported("r2"), reported("r3", None)]}
    page_errors = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))

    def respond(route):
        request = route.request
        parsed = urlparse(request.url)
        path, method = unquote(parsed.path), request.method
        body = request.post_data_json if request.post_data else None
        state["requests"].append((method, path, body, request.headers.get("authorization")))
        if path == "/api/settings":
            if state.get("settings_error"):
                route.fulfill(status=503, json={"detail": "Thiết lập chưa sẵn sàng."})
                return
            settings = dict(SITE_DEFAULTS)
            for key, field in SITE_KEYS.items():
                if key in state["configs"]:
                    value = state["configs"][key]["config_value"]
                    settings[field] = value.lower() == "true" if field == "registration_enabled" else value
            route.fulfill(json=settings)
            return
        if path == "/api/auth/login":
            role = "family_head" if body["email"].startswith("head") else "admin"
            route.fulfill(json={"access_token": f"test-{role}", "user": {
                "id": "same-account", "full_name": "Tài khoản thử", "email": body["email"], "role": role}})
            return
        if state["read_error"] and method == "GET":
            code, detail = state["read_error"]
            route.fulfill(status=code, json={"detail": detail})
            return
        if method != "GET" and state["hold_write"]:
            state["held"].append(route)
            return
        if method != "GET" and state["write_error"]:
            code, detail = state["write_error"]
            if code == 409 and "/verifications/" in path:
                identifier = path.split("/")[-2]
                state["pending"] = [row for row in state["pending"] if row["verification_id"] != identifier]
            if code == 409 and path.endswith("/resolve"):
                identifier = path.split("/")[-2]
                state["reports"] = [row for row in state["reports"] if row["report_id"] != identifier]
            route.fulfill(status=code, json={"detail": detail})
            return
        params = parse_qs(parsed.query)
        if path == "/api/admin/site-settings" and method == "PUT":
            for key, field in SITE_KEYS.items():
                value = str(body[field]).lower() if isinstance(body[field], bool) else body[field]
                state["configs"][key] = {"config_key": key, "config_value": value, "description": "Website setting", "updated_at": "2026-11-20T10:00:00"}
            route.fulfill(json=body)
            return
        offset, limit = int(params.get("offset", [0])[0]), int(params.get("limit", [50])[0])
        if path == "/api/admin/statistics":
            rows = state["statistics"]
            if request.headers.get("authorization") == "Bearer test-family_head":
                rows = rows[:1]
            route.fulfill(json=rows)
            return
        if path == "/api/admin/reports":
            rows = [row for row in state["reports"] if row["status"] == params.get("status", ["pending"])[0]]
            route.fulfill(json=rows[offset:offset + limit])
            return
        if method == "PATCH" and path.endswith("/resolve"):
            identifier = path.split("/")[-2]
            target = next(row for row in state["reports"] if row["report_id"] == identifier)
            affected = [row for row in state["reports"] if row["status"] == "pending"
                        and (row["target_id"] == target["target_id"] if body["decision"] == "resolved" else row is target)]
            for row in affected:
                row["status"] = body["decision"]
                if body["decision"] == "resolved":
                    row["target_content"], row["can_resolve"] = None, False
            if body["decision"] == "resolved":
                state["statistics"][0]["post_count"] -= 1
            route.fulfill(json={"report_id": identifier, "status": body["decision"],
                                "deleted_target_count": int(body["decision"] == "resolved"),
                                "resolved_report_count": len(affected) if body["decision"] == "resolved" else 0})
            return
        if path.startswith("/api/admin/configs"):
            if method == "GET":
                route.fulfill(json=sorted(state["configs"].values(), key=lambda row: row["config_key"])[offset:offset + limit])
            elif method in {"POST", "PUT"}:
                key = body["config_key"] if method == "POST" else path.rsplit("/", 1)[1]
                state["configs"][key] = {"config_key": key, "config_value": body["config_value"],
                                         "description": body.get("description"), "updated_at": "2026-11-12T09:00:00"}
                route.fulfill(status=201 if method == "POST" else 200, json=state["configs"][key])
            else:
                del state["configs"][path.rsplit("/", 1)[1]]
                route.fulfill(status=204)
            return
        if path == "/api/admin/verifications/pending":
            rows = state["pending"]
            if request.headers.get("authorization") == "Bearer test-family_head":
                rows = [row for row in rows if row["branch_name"] == "Chi A"]
            route.fulfill(json=rows[offset:offset + limit])
            return
        if method == "PATCH" and path.endswith("/review"):
            identifier = path.split("/")[-2]
            target = next(row for row in state["pending"] if row["verification_id"] == identifier)
            before = len(state["pending"])
            if body["decision"] == "approved":
                state["pending"] = [row for row in state["pending"]
                                    if row["member_id"] != target["member_id"] and row["user_id"] != target["user_id"]]
            else:
                state["pending"] = [row for row in state["pending"] if row["verification_id"] != identifier]
            route.fulfill(json={"verification_id": identifier, "status": body["decision"],
                                "auto_rejected_count": before - len(state["pending"]) - 1})
            return
        route.fulfill(status=404, json={"detail": "Unexpected test request"})

    # Source modules also contain /api/ in their paths; intercept only the backend prefix.
    context.route(f"{url}/api/**", respond)
    try:
        yield page, state
        assert not page_errors, page_errors
    finally:
        context.close()


def open_as(page, path, role="admin"):
    page.goto("/login")
    page.evaluate("""role => {
        localStorage.setItem('familyconnect.token', `test-${role}`);
        localStorage.setItem('familyconnect.user', JSON.stringify({
            id: 'same-account', fullName: 'Tài khoản thử', email: 'admin@example.com', role
        }));
    }""", role)
    page.goto(path)


def test_config_crud_and_delete_confirmation(ui):
    page, state = ui
    open_as(page, "/admin-config")
    expect(page.get_by_text("Chưa có cấu hình trên trang này.")).to_be_visible()
    page.get_by_label("Tên website", exact=True).fill("Gia phả Việt Nam")
    page.get_by_role("button", name="Lưu thiết lập website", exact=True).click()
    row = page.get_by_role("row").filter(has_text="site.name")
    expect(row).to_contain_text("Gia phả Việt Nam")
    page.get_by_label("Tên website", exact=True).fill("Tên đã sửa")
    page.get_by_role("button", name="Lưu thiết lập website", exact=True).click()
    expect(row).to_contain_text("Tên đã sửa")
    update = next(request for request in state["requests"] if request[0] == "PUT")
    assert set(update[2]) == {"site_name", "logo_url", "theme", "registration_enabled"}
    assert update[3] == "Bearer test-admin"
    assert not any(request[0] == "POST" for request in state["requests"])
    page.once("dialog", lambda dialog: dialog.dismiss())
    row.get_by_role("button", name="Xóa site.name").click()
    assert not any(request[0] == "DELETE" for request in state["requests"])
    page.once("dialog", lambda dialog: dialog.accept())
    row.get_by_role("button", name="Xóa site.name").click()
    expect(row).to_have_count(0)
    expect(page.get_by_label("Tên website", exact=True)).to_have_value("FamilyConnect")


def test_config_page_has_no_manual_key_editor(ui):
    page, state = ui
    open_as(page, "/admin-config")
    expect(page.get_by_label("Tên website", exact=True)).to_be_visible()
    for label in ["Khóa cấu hình", "Giá trị", "Mô tả"]:
        expect(page.get_by_label(label, exact=True)).to_have_count(0)
    expect(page.get_by_role("heading", name="Thêm cấu hình", exact=True)).to_have_count(0)
    expect(page.get_by_role("button", name="Thêm cấu hình", exact=True)).to_have_count(0)
    expect(page.locator("form")).to_have_count(1)
    assert not any(request[0] == "POST" for request in state["requests"])


@pytest.mark.parametrize("label", ["Tên website", "URL logo"])
@pytest.mark.parametrize("invalid", ["", "   "])
def test_config_requires_all_nonblank_fields(ui, label, invalid):
    page, state = ui
    open_as(page, "/admin-config")
    page.get_by_label(label, exact=True).fill(invalid)
    page.get_by_role("button", name="Lưu thiết lập website", exact=True).click()
    expect(page.get_by_role("alert")).to_be_visible()
    assert not any(request[0] == "PUT" for request in state["requests"])


@pytest.mark.parametrize("label", ["Họ và tên", "Email", "Mật khẩu", "Nhập lại mật khẩu"])
@pytest.mark.parametrize("invalid", ["", "        "])
def test_registration_rejects_missing_and_whitespace_fields(ui, label, invalid):
    page, state = ui
    page.goto("/register")
    for name, value in [("Họ và tên", "Test member"), ("Email", "member@example.com"), ("Mật khẩu", "Password!2026"), ("Nhập lại mật khẩu", "Password!2026")]:
        page.get_by_label(name, exact=True).fill(value)
    page.get_by_label(label, exact=True).fill(invalid)
    page.get_by_role("button", name="Đăng ký", exact=True).click()
    expect(page.get_by_role("alert").first).to_be_visible()
    assert not any(request[0] == "POST" for request in state["requests"])


def test_registration_server_validation_is_readable(ui):
    page, _ = ui
    page.route("**/api/auth/register", lambda route: route.fulfill(status=422, json={"detail": [{"loc": ["body", "email"], "msg": "Invalid email"}]}))
    page.goto("/register")
    for name, value in [("Họ và tên", "Test member"), ("Email", "member@example.com"), ("Mật khẩu", "Password!2026"), ("Nhập lại mật khẩu", "Password!2026")]:
        page.get_by_label(name, exact=True).fill(value)
    page.get_by_role("button", name="Đăng ký", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("Dữ liệu chưa hợp lệ")
    expect(page.get_by_role("heading", name="Tạo tài khoản", exact=True)).to_be_visible()


@pytest.mark.parametrize("label", ["Email", "Mật khẩu"])
@pytest.mark.parametrize("invalid", ["", "        "])
def test_login_rejects_missing_and_whitespace_fields(ui, label, invalid):
    page, state = ui
    page.goto("/login")
    page.get_by_label("Email", exact=True).fill("member@example.com")
    page.get_by_label("Mật khẩu", exact=True).fill("Password!2026")
    page.get_by_label(label, exact=True).fill(invalid)
    page.get_by_role("button", name="Đăng nhập", exact=True).click()
    expect(page.get_by_role("alert").first).to_be_visible()
    assert not any(request[0] == "POST" for request in state["requests"])


@pytest.mark.parametrize("code,detail,text", [(409, "Thiết lập đã thay đổi.", "Thiết lập đã thay đổi."),
                                               (422, [{"loc": ["body", "site_name"], "msg": "Too long"}], "Dữ liệu chưa hợp lệ.")])
def test_config_server_errors_preserve_input(ui, code, detail, text):
    page, state = ui
    state["write_error"] = code, detail
    open_as(page, "/admin-config")
    page.get_by_label("Tên website", exact=True).fill("Giữ nội dung")
    page.get_by_role("button", name="Lưu thiết lập website", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text(text)
    expect(page.get_by_label("Tên website", exact=True)).to_have_value("Giữ nội dung")


def test_config_pagination_and_delete_last_row(ui):
    page, state = ui
    for index in range(21):
        key = f"config.{index:02d}"
        state["configs"][key] = {"config_key": key, "config_value": str(index), "description": None, "updated_at": "2026-11-12T09:00:00"}
    open_as(page, "/admin-config")
    expect(page.get_by_role("button", name="Trang sau")).to_be_enabled()
    page.get_by_role("button", name="Trang sau").click()
    expect(page.get_by_role("row").filter(has_text="config.20")).to_be_visible()
    expect(page.get_by_role("button", name="Trang sau")).to_be_disabled()
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name="Xóa config.20").click()
    expect(page.get_by_text("Trang 1", exact=True)).to_be_visible()
    expect(page.get_by_role("row").filter(has_text="config.00")).to_be_visible()


@pytest.mark.parametrize("role,path", [("member", "/admin-config"), ("guest", "/member-approval"), ("family_head", "/admin-config"),
                                      ("family_head", "/reports"), ("member", "/reports"), ("guest", "/reports")])
def test_route_guards_do_not_call_restricted_api(ui, role, path):
    page, state = ui
    open_as(page, path, role)
    expect(page).to_have_url(re.compile(r"/dashboard$"))
    restricted = {"/admin-config": "/api/admin/configs", "/member-approval": "/api/admin/verifications", "/reports": "/api/admin/reports"}[path]
    assert not any(request[1].startswith(restricted) for request in state["requests"])


def test_unauthenticated_and_expired_session_redirect_to_login(ui):
    page, state = ui
    page.goto("/member-approval")
    expect(page).to_have_url(re.compile(r"/login$"))
    state["read_error"] = 401, "Phiên đăng nhập đã hết hạn."
    open_as(page, "/admin-config")
    expect(page).to_have_url(re.compile(r"/login$"))
    assert page.evaluate("localStorage.getItem('familyconnect.token')") is None


def test_approve_refreshes_competing_requests(ui):
    page, state = ui
    open_as(page, "/member-approval")
    page.get_by_role("button", name="Duyệt Nguyễn An", exact=True).click()
    expect(page.get_by_role("row").filter(has_text="Nguyễn An")).to_have_count(0)
    expect(page.get_by_role("row").filter(has_text="Trần Bình")).to_have_count(0)
    expect(page.get_by_role("row").filter(has_text="Lê Chi")).to_be_visible()
    patch = next(request for request in state["requests"] if request[0] == "PATCH")
    assert patch[2] == {"decision": "approved"}


def test_reject_removes_only_selected_request(ui):
    page, _ = ui
    open_as(page, "/member-approval")
    page.get_by_role("button", name="Từ chối Nguyễn An", exact=True).click()
    expect(page.get_by_role("row").filter(has_text="Nguyễn An")).to_have_count(0)
    expect(page.get_by_role("row").filter(has_text="Trần Bình")).to_be_visible()


def test_conflict_refreshes_pending_list(ui):
    page, state = ui
    state["write_error"] = 409, "Yêu cầu xác minh đã được xử lý."
    open_as(page, "/member-approval")
    page.get_by_role("button", name="Duyệt Nguyễn An", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("đã được xử lý")
    expect(page.get_by_role("row").filter(has_text="Nguyễn An")).to_have_count(0)


def test_review_buttons_block_duplicate_submissions(ui):
    page, state = ui
    state["hold_write"] = True
    open_as(page, "/member-approval")
    with page.expect_request("**/api/admin/verifications/a/review"):
        page.get_by_role("button", name="Duyệt Nguyễn An", exact=True).click()
    expect(page.get_by_role("button", name="Từ chối Trần Bình", exact=True)).to_be_disabled()
    expect(page.get_by_role("button", name="Duyệt Nguyễn An", exact=True)).to_be_disabled()
    assert len(state["held"]) == 1
    state["pending"] = [row for row in state["pending"] if row["verification_id"] not in {"a", "b"}]
    state["held"][0].fulfill(json={"verification_id": "a", "status": "approved", "auto_rejected_count": 1})
    expect(page.get_by_role("button", name="Duyệt Lê Chi", exact=True)).to_be_enabled()


def test_logout_and_role_change_do_not_reuse_admin_cache(ui):
    page, _ = ui
    open_as(page, "/member-approval")
    expect(page.get_by_role("row").filter(has_text="Lê Chi")).to_be_visible()
    page.get_by_role("button", name="Đăng xuất", exact=True).click()
    expect(page).to_have_url(re.compile(r"/login$"))
    page.get_by_label("Email", exact=True).fill("head@example.com")
    page.get_by_label("Mật khẩu", exact=True).fill("TestPassword123!")
    page.get_by_role("button", name="Đăng nhập", exact=True).click()
    page.get_by_role("link", name="Duyệt thành viên", exact=True).click()
    expect(page.get_by_role("row").filter(has_text="Nguyễn An")).to_be_visible()
    expect(page.get_by_role("row").filter(has_text="Lê Chi")).to_have_count(0)
    expect(page.get_by_role("link", name="Cấu hình hệ thống", exact=True)).to_have_count(0)


@pytest.mark.parametrize("action", ["logout", "clear"])
def test_logout_is_synced_across_tabs(ui, action):
    page, _ = ui
    open_as(page, "/member-approval")
    other = page.context.new_page()
    other.goto("/member-approval")
    expect(other.get_by_role("row").filter(has_text="Lê Chi")).to_be_visible()
    if action == "logout":
        page.get_by_role("button", name="Đăng xuất", exact=True).click()
    else:
        page.evaluate("localStorage.clear()")
    expect(other).to_have_url(re.compile(r"/login$"))
    expect(other.get_by_role("row").filter(has_text="Lê Chi")).to_have_count(0)
    assert other.evaluate("localStorage.getItem('familyconnect.token')") is None


def test_account_switch_is_synced_across_tabs(ui):
    page, state = ui
    open_as(page, "/member-approval")
    expect(page.get_by_role("row").filter(has_text="Lê Chi")).to_be_visible()
    other = page.context.new_page()
    open_as(other, "/member-approval", "family_head")
    expect(page.get_by_role("row").filter(has_text="Lê Chi")).to_have_count(0)
    expect(page.get_by_role("row").filter(has_text="Nguyễn An")).to_be_visible()
    expect(page.get_by_role("link", name="Cấu hình hệ thống", exact=True)).to_have_count(0)
    assert any(request[1] == "/api/admin/verifications/pending" and request[3] == "Bearer test-family_head"
               for request in state["requests"])


def test_old_401_does_not_clear_new_session(ui):
    page, state = ui
    state["hold_write"] = True
    open_as(page, "/member-approval")
    with page.expect_request("**/api/admin/verifications/a/review"):
        page.get_by_role("button", name="Duyệt Nguyễn An", exact=True).click()
    # The request event can arrive before Playwright dispatches the route handler.
    deadline = time.monotonic() + 5
    while not state["held"] and time.monotonic() < deadline:
        page.wait_for_timeout(10)
    assert state["held"], "The review request was not intercepted."
    assert state["held"][0].request.headers["authorization"] == "Bearer test-admin"
    page.get_by_role("button", name="Đăng xuất", exact=True).click()
    expect(page).to_have_url(re.compile(r"/login$"))
    page.get_by_label("Email", exact=True).fill("head@example.com")
    page.get_by_label("Mật khẩu", exact=True).fill("TestPassword123!")
    page.get_by_role("button", name="Đăng nhập", exact=True).click()
    expect(page.get_by_role("link", name="Duyệt thành viên", exact=True)).to_be_visible()
    assert page.evaluate("localStorage.getItem('familyconnect.token')") == "test-family_head"
    with page.expect_response("**/api/admin/verifications/a/review"):
        state["held"][0].fulfill(status=401, json={"detail": "Phiên cũ đã hết hạn."})
    page.wait_for_load_state("networkidle")
    expect(page.get_by_role("link", name="Duyệt thành viên", exact=True)).to_be_visible()
    assert page.evaluate("localStorage.getItem('familyconnect.token')") == "test-family_head"
    assert page.evaluate("JSON.parse(localStorage.getItem('familyconnect.user')).role") == "family_head"


def test_mobile_layout_and_menu(ui, tmp_path):
    page, _ = ui
    page.set_viewport_size({"width": 390, "height": 844})
    open_as(page, "/admin-config")
    expect(page.get_by_role("heading", name="Cấu hình hệ thống", exact=True)).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.get_by_role("button", name="Mở menu").click()
    page.get_by_role("link", name="Duyệt thành viên", exact=True).click()
    expect(page.get_by_role("heading", name="Duyệt thành viên", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="Đóng menu")).to_have_count(0)
    page.screenshot(path=str(tmp_path / "member-approval-mobile.png"), full_page=True)


@pytest.mark.parametrize("role,families", [("admin", 2), ("family_head", 1)])
def test_dashboard_statistics_chart_and_scope(ui, role, families):
    page, _ = ui
    open_as(page, "/dashboard", role)
    expect(page.get_by_role("table", name="Số liệu hoạt động theo gia đình")).to_be_visible()
    expect(page.get_by_role("row")).to_have_count(families + 1)
    expect(page.get_by_role("row").filter(has_text="Họ Nguyễn")).to_contain_text("6")
    expect(page.get_by_role("img", name="Biểu đồ số thành viên, bài viết và sự kiện theo gia đình")).to_be_visible()
    expect(page.locator(".recharts-wrapper svg").first).to_be_visible()
    if role == "family_head":
        expect(page.get_by_role("row").filter(has_text="Họ Trần")).to_have_count(0)
        expect(page.get_by_role("link", name="Báo cáo nội dung", exact=True)).to_have_count(0)


@pytest.mark.parametrize("role", ["member", "guest"])
def test_member_dashboard_does_not_fetch_statistics(ui, role):
    page, state = ui
    open_as(page, "/dashboard", role)
    expect(page.get_by_role("heading", name="Không gian gia đình", exact=True)).to_be_visible()
    assert not any(request[1] == "/api/admin/statistics" for request in state["requests"])


def test_dashboard_error_refresh_and_empty_state(ui):
    page, state = ui
    state["read_error"] = 503, "Thống kê tạm thời chưa khả dụng."
    open_as(page, "/dashboard")
    expect(page.get_by_role("alert")).to_contain_text("Thống kê tạm thời")
    state["read_error"] = None
    page.get_by_role("button", name="Làm mới", exact=True).click()
    expect(page.get_by_role("table")).to_be_visible()
    state["statistics"] = []
    page.get_by_role("button", name="Làm mới", exact=True).click()
    expect(page.get_by_text("Chưa có gia đình trong phạm vi thống kê của bạn.")).to_be_visible()


def test_dismiss_report_keeps_content_and_escapes_html(ui):
    page, state = ui
    state["reports"][0]["target_content"] = '<script>window.reportInjected=true</script>'
    open_as(page, "/reports")
    card = page.get_by_role("listitem", name="Báo cáo r1", exact=True)
    expect(card).to_contain_text("<script>")
    assert page.evaluate("window.reportInjected === undefined")
    card.get_by_role("button", name="Bỏ qua báo cáo").click()
    expect(page.get_by_role("status")).to_contain_text("Nội dung được giữ nguyên")
    expect(card).to_have_count(0)
    assert state["reports"][0]["target_content"].startswith("<script>")
    patch = next(request for request in state["requests"] if request[0] == "PATCH")
    assert patch[2] == {"decision": "dismissed"} and patch[3] == "Bearer test-admin"
    page.get_by_label("Trạng thái báo cáo").select_option("dismissed")
    expect(card).to_be_visible()
    expect(card.get_by_role("button")).to_have_count(0)


def test_resolve_confirmation_related_reports_and_dashboard_refresh(ui):
    page, _ = ui
    open_as(page, "/dashboard")
    expect(page.get_by_role("row").filter(has_text="Họ Nguyễn").get_by_role("cell").nth(1)).to_have_text("2")
    page.get_by_role("link", name="Báo cáo nội dung", exact=True).click()
    card = page.get_by_role("listitem", name="Báo cáo r1", exact=True)
    page.once("dialog", lambda dialog: dialog.dismiss())
    card.get_by_role("button", name="Gỡ nội dung").click()
    expect(card).to_be_visible()
    page.once("dialog", lambda dialog: dialog.accept())
    card.get_by_role("button", name="Gỡ nội dung").click()
    expect(page.get_by_role("status")).to_contain_text("đóng 2 báo cáo")
    expect(card).to_have_count(0)
    expect(page.get_by_role("listitem", name="Báo cáo r2", exact=True)).to_have_count(0)
    missing = page.get_by_role("listitem", name="Báo cáo r3", exact=True)
    expect(missing.get_by_role("button", name="Gỡ nội dung")).to_be_disabled()
    expect(missing.get_by_role("button", name="Bỏ qua báo cáo")).to_be_enabled()
    page.get_by_role("link", name="Tổng quan", exact=False).click()
    expect(page.get_by_role("row").filter(has_text="Họ Nguyễn").get_by_role("cell").nth(1)).to_have_text("1")


def test_report_conflict_refreshes_list(ui):
    page, state = ui
    state["write_error"] = 409, "Báo cáo đã được xử lý."
    open_as(page, "/reports")
    card = page.get_by_role("listitem", name="Báo cáo r1", exact=True)
    card.get_by_role("button", name="Bỏ qua báo cáo").click()
    expect(page.get_by_role("alert")).to_contain_text("đã được xử lý")
    expect(card).to_have_count(0)


@pytest.mark.parametrize("count", [20, 21])
def test_report_pagination_and_filter_reset(ui, count):
    page, state = ui
    state["reports"] = [reported(f"r{index:02}", f"post-{index}") for index in range(count)]
    open_as(page, "/reports")
    expect(page.get_by_role("listitem")).to_have_count(20)
    if count == 20:
        expect(page.get_by_role("button", name="Trang sau")).to_be_disabled()
    else:
        page.get_by_role("button", name="Trang sau").click()
        expect(page.get_by_role("listitem")).to_have_count(1)
        expect(page.get_by_role("button", name="Trang sau")).to_be_disabled()
        page.get_by_label("Trạng thái báo cáo").select_option("resolved")
        expect(page.get_by_text("Trang 1", exact=True)).to_be_visible()
        expect(page.get_by_text("Không có báo cáo trong trạng thái này.")).to_be_visible()


def test_report_pending_write_blocks_duplicate_actions(ui):
    page, state = ui
    state["hold_write"] = True
    open_as(page, "/reports")
    with page.expect_request("**/api/admin/reports/r1/resolve"):
        page.get_by_role("listitem", name="Báo cáo r1", exact=True).get_by_role("button", name="Bỏ qua báo cáo").click()
    expect(page.get_by_label("Trạng thái báo cáo")).to_be_disabled()
    expect(page.get_by_role("listitem", name="Báo cáo r2", exact=True).get_by_role("button", name="Gỡ nội dung")).to_be_disabled()
    assert len(state["held"]) == 1
    state["reports"][0]["status"] = "dismissed"
    state["held"][0].fulfill(json={"report_id": "r1", "status": "dismissed", "deleted_target_count": 0, "resolved_report_count": 0})
    expect(page.get_by_label("Trạng thái báo cáo")).to_be_enabled()


def test_task8_mobile_layout(ui, tmp_path):
    page, _ = ui
    page.set_viewport_size({"width": 390, "height": 844})
    open_as(page, "/dashboard")
    expect(page.get_by_role("table")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.screenshot(path=str(tmp_path / "dashboard-task8-mobile.png"), full_page=True)
    page.goto("/reports")
    expect(page.get_by_role("listitem")).to_have_count(3)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.screenshot(path=str(tmp_path / "reports-task8-mobile.png"), full_page=True)


@pytest.mark.parametrize("width", [1440, 1024, 768, 390])
def test_website_settings_apply_name_logo_theme_and_registration(ui, tmp_path, width):
    page, state = ui
    page.set_viewport_size({"width": width, "height": 1000})
    open_as(page, "/admin-config")
    page.get_by_label("Tên website", exact=True).fill("Gia phả kiểm thử")
    page.get_by_label("URL logo", exact=True).fill("/assets/icons/ui-award.svg")
    page.get_by_label("Màu giao diện", exact=True).select_option("ocean")
    page.get_by_label("Cho phép đăng ký tài khoản mới", exact=True).uncheck()
    page.get_by_role("button", name="Lưu thiết lập website", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Đã lưu thiết lập website")
    expect(page.locator("html")).to_have_attribute("data-theme", "ocean")
    expect(page).to_have_title(re.compile("^Gia phả kiểm thử"))
    assert page.locator('link[rel="icon"]').get_attribute("href").endswith("/assets/icons/ui-award.svg")
    assert page.get_by_role("button", name="Lưu thiết lập website", exact=True).evaluate("button => getComputedStyle(button).backgroundColor") == "rgb(29, 77, 122)"
    assert len(state["configs"]) == 4
    assert next(row[2] for row in state["requests"] if row[1] == "/api/admin/site-settings")["registration_enabled"] is False
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("heading", name="Cấu hình hệ thống", exact=True).scroll_into_view_if_needed()
    screenshot = tmp_path / f"website-settings-{width}.png"
    page.screenshot(path=str(screenshot), full_page=True)
    print("SETTINGS_SCREENSHOT", str(screenshot))
    page.reload()
    expect(page.get_by_label("Tên website", exact=True)).to_have_value("Gia phả kiểm thử")
    expect(page.get_by_label("Cho phép đăng ký tài khoản mới", exact=True)).not_to_be_checked()
    page.get_by_role("button", name="Đăng xuất", exact=True).click()
    expect(page).to_have_url(re.compile("/login$"))
    expect(page.get_by_role("link", name="Gia phả kiểm thử — trang chủ", exact=True)).to_be_visible()
    expect(page.locator(".brand-mark img")).to_have_attribute("src", "/assets/icons/ui-award.svg")
    expect(page.get_by_role("link", name="Đăng ký", exact=True)).to_have_count(0)
    page.goto("/register")
    expect(page.get_by_role("heading", name="Đăng ký đang tạm đóng", exact=True)).to_be_visible()
    expect(page.get_by_label("Email", exact=True)).to_have_count(0)
    page.goto("/login")
    expect(page.get_by_role("button", name="Đăng nhập", exact=True)).to_be_visible()


@pytest.mark.parametrize("theme,color", [("forest", "rgb(36, 75, 62)"), ("ocean", "rgb(29, 77, 122)"), ("warm", "rgb(115, 66, 40)")])
def test_website_palette_changes_real_controls(ui, theme, color):
    page, _ = ui
    open_as(page, "/admin-config")
    page.get_by_label("Màu giao diện", exact=True).select_option(theme)
    button = page.get_by_role("button", name="Lưu thiết lập website", exact=True)
    button.click()
    expect(page.get_by_role("status")).to_contain_text("Đã lưu thiết lập website")
    assert button.evaluate("element => getComputedStyle(element).backgroundColor") == color


def test_site_settings_save_error_keeps_draft_and_current_brand(ui):
    page, state = ui
    open_as(page, "/admin-config")
    state["write_error"] = 503, "Chưa lưu được thiết lập."
    page.get_by_label("Tên website", exact=True).fill("Bản nháp chưa lưu")
    page.get_by_role("button", name="Lưu thiết lập website", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("Chưa lưu được thiết lập")
    expect(page.get_by_label("Tên website", exact=True)).to_have_value("Bản nháp chưa lưu")
    expect(page).to_have_title(re.compile("^FamilyConnect"))
    assert not state["configs"]
    page.get_by_role("button", name="Hủy thay đổi", exact=True).click()
    expect(page.get_by_label("Tên website", exact=True)).to_have_value("FamilyConnect")
    expect(page.get_by_role("alert")).to_have_count(0)


def test_registration_fails_closed_when_settings_unavailable(ui):
    page, state = ui
    state["settings_error"] = True
    page.goto("/register")
    expect(page.get_by_role("alert")).to_contain_text("Chưa tải được thiết lập đăng ký")
    expect(page.get_by_label("Email", exact=True)).to_have_count(0)
    page.goto("/login")
    expect(page.get_by_role("button", name="Đăng nhập", exact=True)).to_be_visible()


def test_deleted_setting_is_recreated_by_website_form(ui):
    page, state = ui
    open_as(page, "/admin-config")
    page.get_by_label("Màu giao diện", exact=True).select_option("warm")
    page.get_by_role("button", name="Lưu thiết lập website", exact=True).click()
    expect(page.locator("html")).to_have_attribute("data-theme", "warm")
    expect(page.get_by_label("Màu giao diện", exact=True)).to_have_value("warm")
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name="Xóa site.theme", exact=True).click()
    expect(page.locator("html")).to_have_attribute("data-theme", "forest")
    assert "site.theme" not in state["configs"]
    page.get_by_label("Màu giao diện", exact=True).select_option("ocean")
    page.get_by_role("button", name="Lưu thiết lập website", exact=True).click()
    expect(page.locator("html")).to_have_attribute("data-theme", "ocean")
    assert state["configs"]["site.theme"]["config_value"] == "ocean"
    assert not any(request[0] == "POST" for request in state["requests"])


def test_reenabling_registration_restores_register_form(ui):
    page, state = ui
    state["configs"]["registration.enabled"] = dict(config_key="registration.enabled", config_value="false", description="Test registration", updated_at="2026-11-20T10:00:00")
    open_as(page, "/admin-config")
    page.get_by_label("Cho phép đăng ký tài khoản mới", exact=True).check()
    page.get_by_role("button", name="Lưu thiết lập website", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Đã lưu thiết lập website")
    page.get_by_role("button", name="Đăng xuất", exact=True).click()
    page.get_by_role("link", name="Đăng ký", exact=True).click()
    expect(page.get_by_role("heading", name="Tạo tài khoản", exact=True)).to_be_visible()
    expect(page.get_by_label("Email", exact=True)).to_be_visible()
