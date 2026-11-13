"""Browser UI contracts with intercepted HTTP responses. No SQL or real login.

Run with RUN_TASK7_UI=1. HTTP fixtures exist only in this test, never app code.
"""
import json
import re
from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import expect

FAMILY = "00000000-0000-0000-0000-000000000101"
USER = "00000000-0000-0000-0000-000000000201"
MEMBER = "00000000-0000-0000-0000-000000000401"
ITEM = "00000000-0000-0000-0000-000000000301"
TOKEN = "A" * 64


@pytest.fixture
def ui(e2e_browser, vite_server):
    with vite_server() as url:
        context = e2e_browser.new_context(base_url=url, viewport={"width": 1400, "height": 1000})
        page = context.new_page()
        page.set_default_timeout(10000)
        state = {"role": "admin", "requests": [], "error": None, "empty": False, "families_empty": False,
                 "items": [dict(id=ITEM, family_id=FAMILY, created_by_user_id=USER, type="story", title="Ký ức gia đình",
                                description="Lời kể", content="Nội dung ký ức", media_url=None, created_at="2026-11-13T00:00:00", version_token=TOKEN)]}
        def handle(route):
            req = route.request
            path = urlparse(req.url).path
            if not path.startswith("/api/"):
                route.continue_(); return
            params = parse_qs(urlparse(req.url).query)
            body = req.post_data_json if req.post_data else None
            state["requests"].append((req.method, path, params, body))
            if not path.startswith("/api/heritage/"):
                route.fulfill(status=404, json={"detail": "Unexpected API"}); return
            resource = path.split("/")[3]
            identifier = path.split("/")[4] if len(path.split("/")) > 4 else None
            if state["error"]:
                route.fulfill(status=state["error"], json={"detail": "Lỗi API thử nghiệm"}); return
            if resource == "families":
                route.fulfill(json=[] if state["families_empty"] else [dict(id=FAMILY, name="Gia đình thử nghiệm")]); return
            if resource == "family-tree":
                route.fulfill(json=dict(family_id=FAMILY, nodes=[] if state["empty"] else [dict(id=MEMBER, label="Ông An", birth_date="1950-01-01"), dict(id=USER, label="Bà Bình", birth_date=None)],
                                        edges=[] if state["empty"] else [dict(id="marriage-1", source=MEMBER, target=USER, kind="marriage")])); return
            if resource == "members":
                route.fulfill(json=dict(items=[dict(id=MEMBER, full_name="Ông An")], total=1, page=1, page_size=20)); return
            if resource == "ranking":
                route.fulfill(json=dict(items=[dict(member_id=MEMBER, family_id=FAMILY, full_name="Ông An", honor_count=0, rank=1)], total=1, page=1, page_size=12)); return
            if resource == "honors":
                rows = [dict(id=ITEM, member_id=MEMBER, family_id=FAMILY, full_name="Ông An", title="Đóng góp cộng đồng", description=None, date_awarded=None, created_at="2026-11-13T00:00:00", version_token=TOKEN)]
            else: rows = state["items"]
            if req.method == "DELETE":
                state["items"] = [r for r in rows if r["id"] != identifier]
                route.fulfill(status=204); return
            if req.method in ("POST", "PATCH"):
                row = {**state["items"][0], **body}
                row.pop("expected_version", None)
                state["items"] = [row]
                route.fulfill(status=201 if req.method == "POST" else 200, json=row); return
            if identifier:
                route.fulfill(json=rows[0]); return
            if state["empty"]: rows = []
            route.fulfill(json=dict(items=rows, total=len(rows), page=int(params.get("page", [1])[0]), page_size=12))
        page.route("**/api/**", handle)
        def open_as(path="/heritage", role="admin"):
            state["role"] = role
            # Storage priming only; actual login is covered by TV1's gated SQL E2E.
            page.add_init_script("localStorage.setItem('familyconnect.token','ui-test-token');localStorage.setItem('familyconnect.user'," +
                                 json.dumps(json.dumps(dict(id=USER, fullName="TV4", email="tv4@example.invalid", role=role))) + ");")
            page.goto(url + path, wait_until="domcontentloaded", timeout=30000)
        yield page, state, open_as
        context.close()


def test_heritage_detail_edit_and_optimistic_version(ui):
    page, state, open_as = ui
    open_as()
    expect(page.get_by_role("heading", name="Ký ức gia đình", exact=True)).to_be_visible()
    page.get_by_role("button", name="Chi tiết", exact=True).click()
    expect(page.get_by_text("Nội dung ký ức", exact=True)).to_be_visible()
    page.get_by_role("button", name="Sửa", exact=True).click()
    page.get_by_label("Tiêu đề", exact=True).fill("Ký ức được sửa")
    page.get_by_role("button", name="Lưu", exact=True).click()
    expect(page.get_by_role("heading", name="Ký ức được sửa", exact=True)).to_be_visible()
    write = next(call for call in state["requests"] if call[0] == "PATCH")
    assert write[3]["expected_version"] == TOKEN and "actor_id" not in write[3]
    assert write[2]["family_id"] == [FAMILY]


def test_delete_requires_confirmation_and_sends_version(ui):
    page, state, open_as = ui
    open_as()
    page.get_by_role("button", name="Xóa", exact=True).click()
    expect(page.get_by_role("alertdialog")).to_be_visible()
    assert not any(call[0] == "DELETE" for call in state["requests"])
    page.get_by_role("button", name="Xác nhận xóa", exact=True).click()
    expect(page.get_by_text("Chưa có kết quả phù hợp.")).to_be_visible()
    write = next(call for call in state["requests"] if call[0] == "DELETE")
    assert write[2]["expected_version"] == [TOKEN]


def test_member_cannot_manage_honors_but_sees_ranking(ui):
    page, _, open_as = ui
    open_as(role="member")
    page.get_by_role("button", name="Vinh danh", exact=True).click()
    expect(page.get_by_role("heading", name="Đóng góp cộng đồng", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="Thêm vinh danh", exact=True)).to_have_count(0)
    expect(page.get_by_role("button", name="Sửa", exact=True)).to_have_count(0)
    page.get_by_role("button", name="Bảng xếp hạng", exact=True).click()
    expect(page.get_by_role("cell", name="Ông An", exact=True)).to_be_visible()
    expect(page.get_by_role("cell", name="0", exact=True)).to_be_visible()


def test_family_tree_renders_real_contract_and_controls(ui):
    page, state, open_as = ui
    open_as("/family-tree")
    expect(page.get_by_text("Ông An", exact=True)).to_be_visible()
    expect(page.locator(".react-flow__node")).to_have_count(2)
    expect(page.locator(".react-flow__edge")).to_have_count(1)
    expect(page.locator(".react-flow__controls-zoomin")).to_be_visible()
    page.get_by_text("Ông An", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("1950-01-01")
    assert any(call[1] == "/api/heritage/family-tree" for call in state["requests"])


def test_loading_error_retry_and_no_family_state(ui):
    page, state, open_as = ui
    state["error"] = 503
    open_as()
    expect(page.get_by_role("alert")).to_contain_text("Lỗi API thử nghiệm")
    state["error"] = None
    state["families_empty"] = True
    page.get_by_role("button", name="Thử lại", exact=True).click()
    expect(page.get_by_text(re.compile("Chưa có gia đình được liên kết"))).to_be_visible()


def test_mobile_width_has_no_document_overflow(ui):
    page, _, open_as = ui
    page.set_viewport_size({"width": 390, "height": 844})
    open_as()
    expect(page.get_by_role("heading", name="Ký ức gia đình", exact=True)).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


def test_guest_route_guard_does_not_fetch_heritage(ui):
    page, state, open_as = ui
    open_as(role="guest")
    expect(page).to_have_url(re.compile("/dashboard$"))
    assert not any(call[1].startswith("/api/heritage/") for call in state["requests"])


def test_create_story_posts_real_contract(ui):
    page, state, open_as = ui
    open_as()
    page.get_by_role("button", name="Thêm di sản", exact=True).click()
    page.get_by_label("Tiêu đề", exact=True).fill("Câu chuyện mới")
    page.get_by_label("Nội dung", exact=True).fill("Nội dung mới")
    page.get_by_role("button", name="Lưu", exact=True).click()
    expect(page.get_by_role("heading", name="Câu chuyện mới", exact=True)).to_be_visible()
    write = next(call for call in state["requests"] if call[0] == "POST")
    assert write[3] == dict(type="story", title="Câu chuyện mới", content="Nội dung mới", description=None, media_url=None)


def test_unsafe_legacy_media_url_is_not_rendered(ui):
    page, state, open_as = ui
    state["items"][0].update(type="photo", media_url="javascript:alert(1)")
    open_as()
    page.get_by_role("button", name="Chi tiết", exact=True).click()
    expect(page.get_by_role("region", name="Chi tiết")).to_be_visible()
    expect(page.get_by_role("link", name="Mở ảnh / tài liệu", exact=True)).to_have_count(0)
    expect(page.locator("section[aria-label='Chi tiết'] img")).to_have_count(0)
