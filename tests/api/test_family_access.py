"""Authorization regressions: denied requests must not write or call Gemini."""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from test_community_events_api import (  # shared in-memory SQL double
    EVENT_ID, FAMILY_ID, MEMBER_ID, POST_ID, client, session,
)


@pytest.mark.parametrize("method,path,body", [
    ("GET", f"/api/community/posts?family_id={FAMILY_ID}", None),
    ("POST", "/api/community/posts", {"family_id": str(FAMILY_ID), "content": "private"}),
    ("GET", f"/api/community/posts/{POST_ID}", None),
    ("GET", f"/api/community/posts/{POST_ID}/comments", None),
    ("POST", f"/api/community/posts/{POST_ID}/comments", {"content": "private"}),
    ("PUT", f"/api/community/posts/{POST_ID}/reactions", {"type": "Love"}),
    ("POST", "/api/community/reports", {"target_id": str(POST_ID), "target_type": "post", "reason": "private"}),
    ("GET", f"/api/events?family_id={FAMILY_ID}&year=2026&month=11", None),
    ("GET", f"/api/events/{EVENT_ID}", None),
    ("GET", f"/api/events/{EVENT_ID}/gallery", None),
    ("POST", f"/api/events/{EVENT_ID}/gallery", {"media_url": "https://example.com/photo.jpg"}),
    ("POST", f"/api/events/{EVENT_ID}/reminders", {"reminder_time": "2026-11-20T18:30:00"}),
    ("PUT", f"/api/events/{EVENT_ID}/rsvp", {"member_id": str(MEMBER_ID), "rsvp_status": "Going"}),
])
def test_unlinked_user_cannot_read_or_write_family(client, session, method, path, body):
    session.is_member = False
    response = client.request(method, path, json=body)
    assert response.status_code == 403
    assert session.commits == 0
    assert not any("INSERT INTO" in sql or "EXEC community.usp_" in sql for sql, _ in session.statements)


def test_foreign_post_id_cannot_bypass_family_check(client, session):
    session.post_family = uuid4()
    assert client.get(f"/api/community/posts/{POST_ID}").status_code == 403


def test_foreign_event_id_cannot_bypass_family_check(client, session):
    session.event_family = uuid4()
    assert client.get(f"/api/events/{EVENT_ID}/gallery").status_code == 403


def test_rsvp_cannot_impersonate_another_member(client, session):
    session.owns_member = False
    response = client.put(f"/api/events/{EVENT_ID}/rsvp", json={"member_id": str(MEMBER_ID), "rsvp_status": "Going"})
    assert response.status_code == 403
    assert session.last_sql("usp_UpsertEventRsvp") is None
    assert session.commits == 0


@pytest.mark.parametrize("role", ["member", "guest"])
def test_only_family_managers_can_create_events(client, session, role):
    session.user.role = role
    response = client.post("/api/events", json={"family_id": str(FAMILY_ID), "title": "Event", "location": "Test place", "event_date": "2026-11-20T18:30:00"})
    assert response.status_code == 403
    assert session.commits == 0


@pytest.mark.parametrize("path", ["test-embedding", "test-cosine", "chunks"])
def test_ai_routes_require_jwt(path):
    from app.main import app
    with TestClient(app) as anonymous:
        assert anonymous.post(f"/api/ai/{path}", json={}).status_code == 401


@pytest.mark.parametrize("path", ["test-embedding", "test-cosine"])
def test_embedding_test_endpoints_are_admin_only(client, session, monkeypatch, path):
    from app.domains.ai_assistant import services
    monkeypatch.setattr(services, "generate_embedding", lambda _: pytest.fail("Unauthorized Gemini call"))
    assert client.post(f"/api/ai/{path}", json={}).status_code == 403


def test_ai_rejects_foreign_source_before_embedding(client, session, monkeypatch):
    from app.domains.ai_assistant import services
    session.user.role = "family_head"
    session.source_family = uuid4()
    monkeypatch.setattr(services, "generate_embedding", lambda _: pytest.fail("Unauthorized Gemini call"))
    response = client.post("/api/ai/chunks", json={"family_id": str(FAMILY_ID), "source_type": "post", "source_id": str(POST_ID), "chunk_text": "private"})
    assert response.status_code == 403
    assert session.commits == 0


def test_ai_rejects_unlinked_family_before_embedding(client, session, monkeypatch):
    from app.domains.ai_assistant import services
    session.user.role = "family_head"
    session.is_member = False
    monkeypatch.setattr(services, "generate_embedding", lambda _: pytest.fail("Unauthorized Gemini call"))
    response = client.post("/api/ai/chunks", json={"family_id": str(FAMILY_ID), "source_type": "post", "source_id": str(POST_ID), "chunk_text": "private"})
    assert response.status_code == 403
    assert session.commits == 0


def test_member_cannot_write_ai_index(client, session, monkeypatch):
    from app.domains.ai_assistant import services
    monkeypatch.setattr(services, "generate_embedding", lambda _: pytest.fail("Unauthorized Gemini call"))
    response = client.post("/api/ai/chunks", json={"family_id": str(FAMILY_ID), "source_type": "post", "source_id": str(POST_ID), "chunk_text": "private"})
    assert response.status_code == 403
    assert session.commits == 0


def test_manager_can_index_own_family_source(client, session, monkeypatch):
    from app.domains.ai_assistant import services
    session.user.role = "family_head"
    monkeypatch.setattr(services, "generate_embedding", lambda _: [0.1, 0.2])
    response = client.post("/api/ai/chunks", json={"family_id": str(FAMILY_ID), "source_type": "post", "source_id": str(POST_ID), "chunk_text": "allowed"})
    assert response.status_code == 201
    assert response.json()["dimensions"] == 2
    assert session.commits == 1
