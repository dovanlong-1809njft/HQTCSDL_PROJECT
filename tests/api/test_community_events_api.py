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
from datetime import UTC, datetime
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


class FakeSession:
    """Phiên giả: ghi lại mọi câu lệnh và trả dữ liệu dựng sẵn theo từ khóa."""

    def __init__(self) -> None:
        self.statements: list[tuple[str, dict]] = []
        self.commits = 0

    def execute(self, statement, params=None):
        sql = " ".join(str(statement).split())
        self.statements.append((sql, params or {}))

        if "usp_CreatePostWithMedia" in sql:
            return FakeResult([{"PostId": POST_ID}])
        if "vw_NewsfeedPosts" in sql:
            return FakeResult([POST_ROW])
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
            return FakeResult([EVENT_ROW])
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


def test_dat_nhac_nho(client, session):
    response = client.post(
        f"/api/events/{EVENT_ID}/reminders",
        json={"reminder_time": "2026-11-20T18:30:00"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_khong_co_token_thi_bi_chan():
    """Bỏ override get_current_user để kiểm tra API thật sự yêu cầu JWT."""
    from app.main import app

    with TestClient(app) as anonymous:
        response = anonymous.get("/api/community/posts", params={"family_id": str(FAMILY_ID)})

    assert response.status_code in (401, 403)
