"""Real SQL/JWT family isolation; uses the disposable task 6 database only."""
import pytest
from sqlalchemy import text

from test_admin import admin_password_hash, api, headers, sql_database, uid

FAMILY_A, FAMILY_B = uid(1001), uid(1002)
POST_A, POST_B, EVENT_A, EVENT_B = uid(7001), uid(7002), uid(7101), uid(7102)


@pytest.fixture
def family_api(api):
    client, engine, _ = api
    with engine.begin() as connection:
        connection.exec_driver_sql("""
            GRANT SELECT, EXECUTE ON SCHEMA::community TO task6_backend;
            GRANT SELECT, EXECUTE ON SCHEMA::heritage TO task6_backend;
            GRANT INSERT ON community.Events TO task6_backend;
            GRANT INSERT ON community.Comments TO task6_backend;
            GRANT INSERT ON community.EventGalleries TO task6_backend;
            GRANT INSERT ON community.EventReminders TO task6_backend;
            GRANT INSERT ON community.ReportedContents TO task6_backend;
        """).close()
        for post, family, user in [(POST_A, FAMILY_A, uid(9)), (POST_B, FAMILY_B, uid(6))]:
            connection.execute(text("INSERT community.Posts (Id, FamilyId, UserId, Content) VALUES (:id,:family,:user,N'Isolation test')"),
                               {"id": post, "family": family, "user": user})
        for event, family in [(EVENT_A, FAMILY_A), (EVENT_B, FAMILY_B)]:
            connection.execute(text("INSERT community.Events (Id,FamilyId,Title,EventDate) VALUES (:id,:family,N'Isolation test','2026-11-20')"),
                               {"id": event, "family": family})
    try:
        yield client, engine
    finally:
        with engine.begin() as connection:
            for identifier in (POST_A, POST_B):
                connection.execute(text("DELETE heritage.KnowledgeChunks WHERE SourceId=:id"), {"id": identifier})
                connection.execute(text("DELETE community.ReportedContents WHERE TargetId=:id"), {"id": identifier})
                connection.execute(text("DELETE community.Posts WHERE Id=:id"), {"id": identifier})
            for identifier in (EVENT_A, EVENT_B):
                connection.execute(text("DELETE community.Events WHERE Id=:id"), {"id": identifier})
            # The create-event test uses the same isolated fixture and title.
            connection.exec_driver_sql("DELETE community.Events WHERE Title=N'New isolation test'").close()


@pytest.mark.parametrize("method,path,body", [
    ("GET", f"/api/community/posts?family_id={FAMILY_B}", None),
    ("GET", f"/api/community/posts/{POST_B}", None),
    ("POST", f"/api/community/posts/{POST_B}/comments", {"content": "Denied"}),
    ("PUT", f"/api/community/posts/{POST_B}/reactions", {"type": "Love"}),
    ("GET", f"/api/events?family_id={FAMILY_B}&year=2026&month=11", None),
    ("GET", f"/api/events/{EVENT_B}", None),
    ("POST", f"/api/events/{EVENT_B}/gallery", {"media_url": "https://example.com/a.jpg"}),
    ("POST", f"/api/events/{EVENT_B}/reminders", {"reminder_time": "2026-11-20T10:00:00"}),
])
def test_foreign_family_is_denied_with_real_sql(family_api, method, path, body):
    assert family_api[0].request(method, path, json=body, headers=headers(9)).status_code == 403


def test_linked_member_and_admin_can_read_allowed_posts(family_api):
    client, _ = family_api
    assert client.get(f"/api/community/posts/{POST_A}", headers=headers(9)).status_code == 200
    assert client.get(f"/api/community/posts/{POST_B}", headers=headers(1)).status_code == 200


def test_rsvp_must_match_account_and_event_family(family_api):
    client, engine = family_api
    for member in (uid(3010), uid(3012)):
        assert client.put(f"/api/events/{EVENT_A}/rsvp", headers=headers(9), json={"member_id": member, "rsvp_status": "Going"}).status_code == 403
    response = client.put(f"/api/events/{EVENT_A}/rsvp", headers=headers(9), json={"member_id": uid(3014), "rsvp_status": "Going"})
    assert response.status_code == 200, response.text
    with engine.connect() as connection:
        assert connection.execute(text("SELECT COUNT(*) FROM community.EventParticipants WHERE EventId=:id"), {"id": EVENT_A}).scalar_one() == 1


def test_event_creation_requires_manager_in_the_same_family(family_api):
    client, _ = family_api
    body = {"family_id": FAMILY_A, "title": "New isolation test", "location": "Test place", "event_date": "2026-11-20T10:00:00"}
    assert client.post("/api/events", headers=headers(9), json=body).status_code == 403
    assert client.post("/api/events", headers=headers(6), json=body).status_code == 403
    response = client.post("/api/events", headers=headers(2), json=body)
    assert response.status_code == 201, response.text


def test_ai_checks_real_source_family_before_embedding(family_api, monkeypatch):
    from app.domains.ai_assistant import services
    client, _ = family_api
    calls = []
    monkeypatch.setattr(services, "generate_embedding", lambda value: calls.append(value) or [0.1, 0.2])
    body = {"family_id": FAMILY_A, "source_type": "post", "source_id": POST_B, "chunk_text": "Test"}
    assert client.post("/api/ai/chunks", headers=headers(2), json=body).status_code == 403
    assert calls == []
    body["source_id"] = POST_A
    response = client.post("/api/ai/chunks", headers=headers(2), json=body)
    assert response.status_code == 201, response.text
    assert calls == ["Test"]
