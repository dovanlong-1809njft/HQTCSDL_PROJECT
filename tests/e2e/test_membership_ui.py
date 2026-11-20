"""Browser interactions with HTTP fixtures; SQL contracts live in test_membership_sql."""
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import expect

FAMILY="00000000-0000-0000-0000-000000000101"
USER="00000000-0000-0000-0000-000000000201"
FIRST="00000000-0000-0000-0000-000000000301"
SECOND="00000000-0000-0000-0000-000000000302"


@pytest.fixture
def membership_ui(e2e_browser,vite_server):
    with vite_server() as url:
        context=e2e_browser.new_context(base_url=url,viewport={"width":1440,"height":1000})
        page=context.new_page()
        page.set_default_timeout(10000)
        page.on("pageerror",lambda error: print("BROWSER ERROR:",str(error)))
        state={"writes":[],"families":[dict(id=FAMILY,name="Gia đình kiểm thử")],"members":[dict(id=FIRST,name="Nguyễn An",branch_id=None,birth_date="1960-01-01",location=None,user_id=None),dict(id=SECOND,name="Nguyễn Bình",branch_id=None,birth_date="1990-01-01",location=None,user_id=None)],"branches":[],"edges":[],"profile":dict(user=dict(id=USER,full_name="Nguyễn An",email="ui@example.com",role="admin"),member=None,verifications=[])}
        def handle(route):
            req=route.request
            path=urlparse(req.url).path
            if not path.startswith("/api/"):
                route.continue_(); return
            params=parse_qs(urlparse(req.url).query)
            body=req.post_data_json if req.post_data else None
            if req.method!="GET": state["writes"].append((req.method,path,body))
            if path=="/api/heritage/families": route.fulfill(json=state["families"]); return
            if path=="/api/heritage/family-tree":
                route.fulfill(json=dict(family_id=FAMILY,nodes=[dict(id=m["id"],label=m["name"],birth_date=m["birth_date"]) for m in state["members"]],edges=[dict(id=e["id"],source=e["first_id"],target=e["second_id"],kind="parent_child") for e in state["edges"]])); return
            if path=="/api/genealogy/me":
                if req.method=="PUT": state["profile"]["user"]["full_name"]=body["name"]
                route.fulfill(json=state["profile"]); return
            if path=="/api/genealogy/verification-candidates": route.fulfill(json=[dict(id=FIRST,name="Nguyễn An",family_name="Gia đình kiểm thử",branch_name=None)]); return
            if path=="/api/genealogy/verifications":
                state["profile"]["verifications"]=[dict(id="request-one",status="pending",name="Nguyễn An",family_name="Gia đình kiểm thử")]
                route.fulfill(status=201,json=state["profile"]); return
            if path=="/api/genealogy/relationships": route.fulfill(json=dict(parent_child=state["edges"],marriages=[],ancestors=[dict(id=FIRST,name="Nguyễn An",depth=1)] if state["edges"] else [],descendants=[])); return
            if path.startswith("/api/genealogy/relationships/parent-child"):
                if req.method=="POST":
                    state["edges"].append(dict(id="edge-one",first_id=FIRST,second_id=SECOND,first_name="Nguyễn An",second_name="Nguyễn Bình"))
                    route.fulfill(status=201,json={"id":"edge-one"})
                else: state["edges"]=[]; route.fulfill(status=204)
                return
            if path.startswith("/api/genealogy/members") or path.startswith("/api/genealogy/branches"):
                resource=path.split("/")[3]
                if req.method=="GET":
                    rows=[r for r in state[resource] if params.get("q",[""])[0].lower() in r["name"].lower()]
                    route.fulfill(json=dict(items=rows,total=len(rows))); return
                if req.method=="POST":
                    identifier="new-"+resource
                    state[resource].append(dict(id=identifier,**body,user_id=None))
                    route.fulfill(status=201,json={"id":identifier}); return
                identifier=path.rsplit("/",1)[1]
                if req.method=="DELETE": state[resource]=[r for r in state[resource] if r["id"]!=identifier]; route.fulfill(status=204); return
                next(r for r in state[resource] if r["id"]==identifier).update(body)
                route.fulfill(json={"id":identifier}); return
            route.fulfill(status=404,json={"detail":"Unexpected API fixture"})
        page.route("**/api/**",handle)
        context.add_init_script("localStorage.setItem('familyconnect.token','ui-test-token');localStorage.setItem('familyconnect.user',"+json.dumps(json.dumps(dict(id=USER,fullName="Nguyễn An",email="ui@example.com",role="admin")))+");")
        try: yield page,state,url
        finally: context.close()


def test_profile_save_and_request_verification(membership_ui):
    page,state,_=membership_ui
    page.goto("/profile")
    expect(page.get_by_role("heading",name="Hồ sơ của tôi",exact=True)).to_be_visible()
    page.get_by_label("Họ và tên",exact=True).fill("Nguyễn An Mới")
    page.get_by_role("button",name="Lưu hồ sơ",exact=True).click()
    expect(page.get_by_role("status").filter(has_text="Đã lưu hồ sơ")).to_be_visible()
    expect(page.locator(".account-info")).to_contain_text("Nguyễn An Mới")
    page.get_by_label("Tên gia đình",exact=True).fill("Gia đình kiểm thử")
    page.get_by_role("button",name="Tìm hồ sơ",exact=True).click()
    page.get_by_role("button",name="Gửi yêu cầu xác minh",exact=True).click()
    expect(page.get_by_text("Chờ duyệt",exact=True)).to_be_visible()
    expect(page.get_by_role("button",name="Tìm hồ sơ",exact=True)).to_be_disabled()
    assert state["writes"][-1][2]=={"member_id":FIRST}


def test_member_create_edit_delete(membership_ui):
    page,state,_=membership_ui
    state["branches"]=[dict(id="test-branch",name="Chi kiểm thử",can_manage=True)]
    page.goto("/family-management")
    page.get_by_label("Họ và tên",exact=True).fill("Thành viên mới")
    page.get_by_label("Ngày sinh",exact=True).fill("2001-02-03")
    page.get_by_label("Chi nhánh",exact=True).select_option("test-branch")
    page.get_by_label("Nơi ở",exact=True).fill("Hà Nội")
    page.get_by_role("button",name="Thêm mới",exact=True).click()
    row=page.get_by_role("listitem").filter(has_text="Thành viên mới")
    expect(row).to_be_visible()
    row.get_by_role("button",name="Sửa",exact=False).click()
    page.get_by_label("Họ và tên",exact=True).fill("Thành viên đã sửa")
    page.get_by_role("button",name="Lưu thay đổi",exact=True).click()
    row=page.get_by_role("listitem").filter(has_text="Thành viên đã sửa")
    expect(row).to_be_visible()
    page.once("dialog",lambda dialog:dialog.accept())
    row.get_by_role("button",name="Xóa",exact=False).click()
    expect(row).to_have_count(0)
    writes=[entry for entry in state["writes"] if "/members" in entry[1]]
    assert [entry[0] for entry in writes]==["POST","PUT","DELETE"]
    assert writes[0][2]["birth_date"]=="2001-02-03"


@pytest.mark.parametrize("field,invalid", [("name", ""), ("name", "   "), ("branch_id", ""), ("birth_date", ""), ("location", ""), ("location", "   ")])
def test_member_form_blocks_incomplete_data(membership_ui, field, invalid):
    page,state,_=membership_ui
    state["branches"]=[dict(id="test-branch",name="Chi kiểm thử",can_manage=True)]
    page.goto("/family-management")
    page.get_by_label("Họ và tên",exact=True).fill("Test member")
    page.get_by_label("Chi nhánh",exact=True).select_option("test-branch")
    page.get_by_label("Ngày sinh",exact=True).fill("1990-01-01")
    page.get_by_label("Nơi ở",exact=True).fill("Hà Nội")
    control=page.get_by_label("Họ và tên",exact=True) if field=="name" else page.locator(f'[name="{field}"]')
    control.select_option(invalid) if field=="branch_id" else control.fill(invalid)
    page.get_by_role("button",name="Thêm mới",exact=True).click()
    assert control.evaluate("field => !field.validity.valid")
    assert not state["writes"]
    control.select_option("test-branch") if field=="branch_id" else control.fill("1990-01-01" if field=="birth_date" else "Valid value")
    page.get_by_role("button",name="Thêm mới",exact=True).click()
    expect(page.get_by_role("status").filter(has_text="Đã lưu dữ liệu")).to_be_visible()
    assert len(state["writes"])==1


@pytest.mark.parametrize("field", ["birth_date", "location"])
def test_linked_profile_requires_birth_date_and_location(membership_ui, field):
    page,state,_=membership_ui
    state["profile"]["member"]=dict(id=FIRST,name="Nguyễn An",family_name="Gia đình kiểm thử",branch_name="Chi kiểm thử",birth_date="1990-01-01",location="Hà Nội")
    page.goto("/profile")
    control=page.locator(f'[name="{field}"]')
    control.fill("")
    page.get_by_role("button",name="Lưu hồ sơ",exact=True).click()
    assert control.evaluate("field => !field.validity.valid")
    assert not state["writes"]


def test_marriage_requires_date(membership_ui):
    page,state,_=membership_ui
    page.goto("/family-tree")
    page.get_by_label("Loại quan hệ",exact=True).select_option("marriages")
    page.get_by_label("Người thứ nhất",exact=True).select_option(FIRST)
    page.get_by_label("Người thứ hai",exact=True).select_option(SECOND)
    page.get_by_role("button",name="Thêm quan hệ",exact=True).click()
    assert page.get_by_label("Ngày kết hôn",exact=True).evaluate("field => !field.validity.valid")
    assert not state["writes"]


def test_relation_change_refreshes_tree_and_queries_ancestors(membership_ui):
    page,state,_=membership_ui
    page.goto("/family-tree")
    page.get_by_label("Cha/mẹ",exact=True).select_option(FIRST)
    page.get_by_label("Con",exact=True).select_option(SECOND)
    page.get_by_role("button",name="Thêm quan hệ",exact=True).click()
    expect(page.get_by_text("Nguyễn An → Nguyễn Bình",exact=True)).to_be_visible()
    expect(page.locator(".react-flow__edge")).to_have_count(1)
    page.get_by_label("Thành viên cần tra cứu",exact=True).select_option(SECOND)
    expect(page.get_by_text("Nguyễn An · cách 1 đời",exact=True)).to_be_visible()
    page.once("dialog",lambda dialog:dialog.accept())
    page.get_by_role("button",name="Xóa quan hệ Nguyễn An và Nguyễn Bình",exact=True).click()
    expect(page.locator(".react-flow__edge")).to_have_count(0)
    assert state["writes"][0][2]["first_id"]==FIRST


def test_head_management_stays_in_own_branch(membership_ui):
    page,state,_=membership_ui
    state["profile"]["user"]["role"]="family_head"
    state["profile"]["member"]=dict(id=FIRST,name="Nguyễn An",family_name="Gia đình kiểm thử",family_id=FAMILY,branch_id="own-branch",branch_name="Chi của tôi",birth_date=None,location=None)
    state["branches"]=[dict(id="own-branch",name="Chi của tôi",can_manage=True),dict(id="other-branch",name="Chi khác",can_manage=False)]
    state["members"][0]["can_manage"]=True
    state["members"][1]["can_manage"]=False
    page.goto("/profile")
    page.evaluate("user => {localStorage.setItem('familyconnect.user',JSON.stringify(user));window.dispatchEvent(new StorageEvent('storage',{storageArea:localStorage,key:'familyconnect.user'}));}",dict(id=USER,fullName="Nguyễn An",email="ui@example.com",role="family_head"))
    page.get_by_role("link",name="Gia đình và thành viên",exact=True).click()
    expect(page.get_by_role("button",name="Tạo gia đình",exact=True)).to_have_count(0)
    expect(page.get_by_role("button",name="Sửa Nguyễn An",exact=True)).to_be_visible()
    expect(page.get_by_role("button",name="Sửa Nguyễn Bình",exact=True)).to_have_count(0)
    expect(page.get_by_role("combobox",name="Chi nhánh",exact=True)).to_have_value("own-branch")
    expect(page.get_by_role("combobox",name="Chi nhánh",exact=True).get_by_role("option",name="Chi khác",exact=True)).to_have_count(0)


@pytest.mark.parametrize("width",[1440,1024,768,390])
@pytest.mark.parametrize("path",["/profile","/family-management","/family-tree"])
def test_responsive_layout_and_drawer_keyboard(membership_ui,path,width):
    page,_,_=membership_ui
    page.set_viewport_size({"width":width,"height":900 if width>=1024 else 844})
    page.goto(path)
    expect(page.get_by_role("heading",level=1)).to_be_visible()
    if width<1024:
        page.get_by_role("button",name="Mở menu",exact=True).click()
        expect(page.get_by_role("dialog",name="Điều hướng chính")).to_be_visible()
        page.keyboard.press("Escape")
        expect(page.get_by_role("dialog",name="Điều hướng chính")).to_have_count(0)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    output=Path(__file__).resolve().parents[2]/"apps/web/.taste-skill/shots"
    output.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(output/(path.strip("/")+f"-{width}.png")),full_page=True)
