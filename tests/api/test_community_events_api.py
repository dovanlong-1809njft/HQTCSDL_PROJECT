"""Kiểm thử API phân hệ Cộng đồng & Sự kiện (TV3) mà không cần SQL Server.

Mỗi lần test, lớp FakeSession thay cho phiên SQLAlchemy thật: nó ghi lại câu
lệnh đã chạy và trả về dữ liệu dựng sẵn. Nhờ vậy test kiểm tra được đường dẫn
API, việc kiểm tra JWT, hình dạng dữ liệu trả về và đúng Stored Procedure nào
được gọi. Phần SQL chạy thật đã có kịch bản riêng ở tests/database/.

Chạy:
    cd apps/backend
    JWT_SECRET_KEY=test python -m pytest ../../tests/api -q
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime,timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[2] / "apps" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

FAMILY_ID = UUID("11111111-1111-1111-1111-111111111111")
USER_ID = UUID("22222222-2222-2222-2222-222222222222")
POST_ID = UUID("33333333-3333-3333-3333-333333333333")
EVENT_ID = UUID("44444444-4444-4444-4444-444444444444")
MEMBER_ID = UUID("55555555-5555-5555-5555-555555555555")
NOW = datetime(2026, 11, 20, 10, 30, tzinfo=UTC)

POST_ROW = {
    "PostId": POST_ID,
    "FamilyId": FAMILY_ID,
    "AuthorId": USER_ID,
    "AuthorName": "Nguyễn Duy Long",
    "Content": "Bài viết thử",
    "CreatedAt": NOW,
    "CommentCount": 2,
    "ReactionCount": 5,
    "MediaUrls": "https://a.jpg,https://b.jpg",
}
EVENT_ROW = {
    "EventId": EVENT_ID,
    "FamilyId": FAMILY_ID,
    "Title": "Giỗ tổ",
    "EventDate": NOW,
    "Location": "Nhà thờ họ",
    "GoingCount": 3,
}


class FakeResult:
    def __init__(self, rows: list[dict] | None = None, scalar=None) -> None:
        self._rows = rows or []
        self._scalar = scalar

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def one(self):
        return self._rows[0]

    def one_or_none(self):
        return self._rows[0] if self._rows else None

    def scalar(self):
        return self._scalar

    def scalar_one(self):
        return self._scalar

    def scalar_one_or_none(self):
        return self._scalar


class FakeSession:
    """Phiên giả: ghi lại mọi câu lệnh và trả dữ liệu dựng sẵn theo từ khóa."""

    def __init__(self) -> None:
        self.statements: list[tuple[str, dict]] = []
        self.commits = 0
        self.is_member = True
        self.owns_member = True
        self.source_family = FAMILY_ID
        self.post_family = FAMILY_ID
        self.event_family = FAMILY_ID

    def execute(self, statement, params=None):
        sql = " ".join(str(statement).split())
        self.statements.append((sql, params or {}))

        if "AS IsMember" in sql:
            return FakeResult([{"Id": params["family_id"], "IsMember": self.is_member and params["family_id"] == str(FAMILY_ID)}])
        if "SELECT 1 FROM genealogy.Members" in sql:
            return FakeResult(scalar=1 if self.owns_member and params["member_id"] == str(MEMBER_ID) else None)
        if "SELECT FamilyId FROM" in sql:
            return FakeResult(scalar=self.source_family)
        if "SELECT p.FamilyId FROM" in sql:
            return FakeResult(scalar=self.post_family)

        if "usp_CreatePostWithMedia" in sql:
            return FakeResult([{"PostId": POST_ID}])
        if "usp_UpsertKnowledgeChunk" in sql:
            return FakeResult([{"ChunkId": uuid4(), "ActionTaken": "INSERT"}])
        if "vw_NewsfeedPosts" in sql:
            return FakeResult([{**POST_ROW, "FamilyId": self.post_family}])
        if "COUNT_BIG(*) FROM community.Posts" in sql:
            return FakeResult(scalar=1)
        if "COUNT_BIG(*) FROM community.Reactions" in sql:
            return FakeResult(scalar=6)
        if "INSERT INTO community.Comments" in sql:
            return FakeResult(
                [
                    {
                        "Id": uuid4(),
                        "PostId": POST_ID,
                        "UserId": USER_ID,
                        "Content": params["content"],
                        "CreatedAt": NOW,
                    }
                ]
            )
        if "INSERT INTO community.ReportedContents" in sql:
            return FakeResult(
                [
                    {
                        "Id": uuid4(),
                        "TargetId": UUID(params["target_id"]),
                        "TargetType": params["target_type"],
                        "Status": "pending",
                        "CreatedAt": NOW,
                    }
                ]
            )
        if "fn_GetMonthlyEvents" in sql or "FROM community.Events" in sql:
            return FakeResult([{**EVENT_ROW, "FamilyId": self.event_family}])
        if "usp_UpsertReaction" in sql or "usp_UpsertEventRsvp" in sql:
            return FakeResult()
        if "INSERT INTO community.EventReminders" in sql:
            return FakeResult(
                [
                    {
                        "Id": uuid4(),
                        "EventId": EVENT_ID,
                        "ReminderTime": NOW,
                        "Status": "pending",
                    }
                ]
            )
        return FakeResult()

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:  # pragma: no cover - chỉ dùng khi có lỗi
        pass

    def close(self) -> None:
        pass

    def last_sql(self, keyword: str) -> str | None:
        for sql, _ in reversed(self.statements):
            if keyword in sql:
                return sql
        return None

    def params_of(self, keyword: str) -> dict:
        for sql, params in reversed(self.statements):
            if keyword in sql:
                return params
        return {}


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def client(session: FakeSession, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")

    from app.core.database import get_db
    from app.core.security import get_current_user
    from app.domains.identity.models import User
    from app.main import app

    fake_user = User(
        id=USER_ID,
        email="tv3@example.invalid",
        password_hash="x",
        full_name="Nguyễn Duy Long",
        role="member",
        is_active=True,
    )
    session.user = fake_user

    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_tao_bai_viet_goi_dung_stored_procedure(client, session):
    response = client.post(
        "/api/community/posts",
        json={
            "family_id": str(FAMILY_ID),
            "content": "Bài viết thử",
            "media": [{"url": "https://a.jpg"}, {"url": "https://b.jpg", "type": "image"}],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["post_id"] == str(POST_ID)
    # View trả MediaUrls nối bằng dấu phẩy, API phải tách thành danh sách
    assert body["media_urls"] == ["https://a.jpg", "https://b.jpg"]

    assert session.last_sql("usp_CreatePostWithMedia") is not None
    params = session.params_of("usp_CreatePostWithMedia")
    assert params["user_id"] == str(USER_ID)   # tác giả lấy từ JWT, không từ body
    assert '"url": "https://a.jpg"' in params["media_json"]


def test_bang_tin_doc_tu_view(client, session):
    response = client.get("/api/community/posts", params={"family_id": str(FAMILY_ID)})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["author_name"] == "Nguyễn Duy Long"
    assert "vw_NewsfeedPosts" in session.last_sql("vw_NewsfeedPosts")


def test_tha_cam_xuc_goi_merge(client, session):
    response = client.put(
        f"/api/community/posts/{POST_ID}/reactions", json={"type": "Love"}
    )

    assert response.status_code == 200
    assert response.json()["reaction_count"] == 6
    assert session.params_of("usp_UpsertReaction")["reaction_type"] == "Love"


def test_go_cam_xuc_gui_type_null(client, session):
    response = client.put(f"/api/community/posts/{POST_ID}/reactions", json={"type": None})

    assert response.status_code == 200
    assert session.params_of("usp_UpsertReaction")["reaction_type"] is None


def test_bao_cao_noi_dung_sai_loai_bi_tu_choi(client):
    response = client.post(
        "/api/community/reports",
        json={"target_id": str(POST_ID), "target_type": "video", "reason": "spam"},
    )

    assert response.status_code == 422  # chỉ nhận post | comment | photo


def test_lich_thang_goi_function(client, session):
    response = client.get(
        "/api/events",
        params={"family_id": str(FAMILY_ID), "year": 2026, "month": 11},
    )

    assert response.status_code == 200
    assert response.json()[0]["going_count"] == 3
    assert session.params_of("fn_GetMonthlyEvents")["month"] == 11


def test_rsvp_goi_stored_procedure(client, session):
    response = client.put(
        f"/api/events/{EVENT_ID}/rsvp",
        json={"member_id": str(MEMBER_ID), "rsvp_status": "Going"},
    )

    assert response.status_code == 200
    params = session.params_of("usp_UpsertEventRsvp")
    assert params["member_id"] == str(MEMBER_ID)
    assert params["rsvp_status"] == "Going"


def test_rsvp_sai_trang_thai_bi_tu_choi(client):
    response = client.put(
        f"/api/events/{EVENT_ID}/rsvp",
        json={"member_id": str(MEMBER_ID), "rsvp_status": "Thich thi di"},
    )

    assert response.status_code == 422


def test_dat_nhac_nho(client, session,monkeypatch):
    event_time=datetime.now(UTC)+timedelta(days=7)
    monkeypatch.setitem(EVENT_ROW,"EventDate",event_time)
    response = client.post(
        f"/api/events/{EVENT_ID}/reminders",
        json={"reminder_time": (event_time-timedelta(hours=1)).isoformat()},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_khong_co_token_thi_bi_chan():
    """Bỏ override get_current_user để kiểm tra API thật sự yêu cầu JWT."""
    from app.main import app

    with TestClient(app) as anonymous:
        response = anonymous.get("/api/community/posts", params={"family_id": str(FAMILY_ID)})

    assert response.status_code in (401, 403)


@pytest.mark.parametrize("method,path,payload,required", [
    ("POST", "/api/auth/register", dict(full_name="Test member", email="member@example.com", password="Password!2026"), ("full_name", "email", "password")),
    ("POST", "/api/auth/login", dict(email="member@example.com", password="Password!2026"), ("email", "password")),
    ("POST", "/api/admin/configs", dict(config_key="test.required", config_value="value", description="Test config"), ("config_key", "config_value", "description")),
    ("PUT", "/api/admin/configs/test.required", dict(config_value="value", description="Test config"), ("config_value", "description")),
    ("POST", "/api/events", dict(family_id=str(FAMILY_ID), title="Test event", event_date="2027-01-01T10:00:00", location="Test place"), ("family_id", "title", "event_date", "location")),
    ("PUT", f"/api/events/{EVENT_ID}", dict(title="Test event", event_date="2027-01-01T10:00:00", location="Test place"), ("title", "event_date", "location")),
    ("POST", f"/api/genealogy/members?family_id={FAMILY_ID}", dict(name="Test member", branch_id=str(FAMILY_ID), birth_date="1990-01-01", location="Test place"), ("name", "branch_id", "birth_date", "location")),
    ("PUT", f"/api/genealogy/members/{MEMBER_ID}?family_id={FAMILY_ID}", dict(name="Test member", branch_id=str(FAMILY_ID), birth_date="1990-01-01", location="Test place"), ("name", "branch_id", "birth_date", "location")),
    ("PUT", "/api/genealogy/me", dict(name="Test member", birth_date="1990-01-01", location="Test place"), ("name", "birth_date", "location")),
    ("POST", f"/api/genealogy/relationships/marriages?family_id={FAMILY_ID}", dict(first_id=str(USER_ID), second_id=str(MEMBER_ID), married_date="2020-01-01"), ("first_id", "second_id", "married_date")),
    ("POST", f"/api/directory/{MEMBER_ID}/educations", dict(institution="Test school", degree="Test degree", start_date="2020-01-01"), ("institution", "degree", "start_date")),
    ("PUT", f"/api/directory/{MEMBER_ID}/work/{USER_ID}", dict(company="Test company", position="Test job", start_date="2020-01-01"), ("company", "position", "start_date")),
    ("POST", f"/api/heritage/items?family_id={FAMILY_ID}", dict(type="story", title="Test story", description="Test description", content="Test content"), ("type", "title", "description", "content")),
    ("POST", f"/api/heritage/honors?family_id={FAMILY_ID}", dict(member_id=str(MEMBER_ID), title="Test honor", description="Test description", date_awarded="2020-01-01"), ("member_id", "title", "description", "date_awarded")),
    ("POST", "/api/community/posts", dict(family_id=str(FAMILY_ID), content="Test content"), ("family_id", "content")),
    ("POST", f"/api/community/posts/{POST_ID}/comments", dict(content="Test comment"), ("content",)),
    ("POST", "/api/community/reports", dict(target_id=str(POST_ID), target_type="post", reason="Test reason"), ("target_id", "target_type", "reason")),
    ("POST", f"/api/events/{EVENT_ID}/gallery", dict(media_url="https://example.com/photo.jpg"), ("media_url",)),
    ("POST", f"/api/events/{EVENT_ID}/reminders", dict(reminder_time="2027-01-01T09:00:00"), ("reminder_time",)),
])
@pytest.mark.parametrize("invalid", ["missing", None, "", " \t\n\u00a0 "])
def test_required_web_inputs_cannot_bypass_api(client, session, monkeypatch, method, path, payload, required, invalid):
    from app.domains.genealogy import repository
    session.user.role = "admin"
    monkeypatch.setattr(repository, "profile", lambda *_: {"member": {"id": str(MEMBER_ID)}})
    for field in required:
        body = dict(payload)
        if invalid == "missing":
            del body[field]
        else:
            body[field] = invalid
        response = client.request(method, path, json=body)
        assert response.status_code == 422, (path, field, invalid, response.text)
    assert session.commits == 0
    assert not session.statements


def test_valid_registration_trims_name_but_preserves_password():
    from app.domains.identity.schemas import RegisterRequest
    payload = RegisterRequest(full_name="  Test member  ", email="member@example.com", password=" Password!2026 ")
    assert payload.full_name == "Test member"
    assert payload.password == " Password!2026 "
