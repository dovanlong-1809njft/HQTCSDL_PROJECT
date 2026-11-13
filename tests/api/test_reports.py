"""Task 8: reuse the isolated SQL Server + JWT fixtures from task 6."""
import pytest
from sqlalchemy import text

from test_admin import (ROOT, admin_password_hash, api, execute_script, headers,
                        scalar, sql_database, uid)


@pytest.fixture
def reports_api(api):
    client, engine, options = api
    with engine.begin() as connection:
        execute_script(connection, (ROOT / "tests/database/task8.integration.sql").read_text(encoding="utf-8"),
                       engine.url.database)
    try:
        yield client, engine, options
    finally:
        with engine.begin() as connection:
            connection.exec_driver_sql("DELETE community.ReportedContents; DELETE community.Posts; DELETE community.Events;").close()


ENDPOINTS = [
    ("GET", "/api/admin/statistics", None),
    ("GET", "/api/admin/reports", None),
    ("PATCH", f"/api/admin/reports/{uid(6001)}/resolve", {"decision": "resolved"}),
]


@pytest.mark.parametrize("method,path,body", ENDPOINTS)
def test_reporting_endpoints_require_jwt(reports_api, method, path, body):
    assert reports_api[0].request(method, path, json=body).status_code == 401


@pytest.mark.parametrize("method,path,body", ENDPOINTS)
@pytest.mark.parametrize("user", [3, 4])
def test_member_and_guest_cannot_use_reporting_api(reports_api, method, path, body, user):
    assert reports_api[0].request(method, path, json=body, headers=headers(user)).status_code == 403


@pytest.mark.parametrize("method,path,body", ENDPOINTS[1:])
def test_family_head_cannot_moderate(reports_api, method, path, body):
    assert reports_api[0].request(method, path, json=body, headers=headers(2)).status_code == 403


@pytest.mark.parametrize("user,expected", [(1, {1001, 1002, 1003}), (2, {1001}), (6, {1002}), (7, {1001})])
def test_statistics_scope_and_exact_counts(reports_api, user, expected):
    response = reports_api[0].get("/api/admin/statistics", headers=headers(user))
    assert response.status_code == 200, response.text
    rows = {row["family_id"]: row for row in response.json()}
    assert set(rows) == {uid(value) for value in expected}
    counts = {1001: (7, 2, 2), 1002: (2, 1, 1), 1003: (0, 0, 0)}
    for value in expected:
        assert tuple(rows[uid(value)][key] for key in ("member_count", "post_count", "event_count")) == counts[value]


def test_unlinked_head_has_no_statistics(reports_api):
    client, engine, _ = reports_api
    with engine.begin() as connection:
        connection.execute(text("UPDATE genealogy.Members SET UserId = NULL WHERE UserId = :id"), {"id": uid(7)})
    assert client.get("/api/admin/statistics", headers=headers(7)).json() == []


def test_report_list_content_types_missing_targets_and_pagination(reports_api):
    client, _, _ = reports_api
    response = client.get("/api/admin/reports", headers=headers())
    assert response.status_code == 200, response.text
    rows = {row["report_id"]: row for row in response.json()}
    assert len(rows) == 7
    assert rows[uid(6001)]["target_content"] == "Bài viết cần kiểm duyệt"
    assert rows[uid(6003)]["target_type"] == "comment"
    assert rows[uid(6004)]["target_content"] == "https://example.invalid/image.jpg"
    assert rows[uid(6004)]["can_resolve"] is True
    assert rows[uid(6006)]["target_content"] is None
    assert rows[uid(6006)]["can_resolve"] is rows[uid(6007)]["can_resolve"] is False
    assert rows[uid(6001)]["family_name"] == "Family A"
    assert "password_hash" not in response.text
    first = client.get("/api/admin/reports?limit=2", headers=headers()).json()
    second = client.get("/api/admin/reports?limit=2&offset=2", headers=headers()).json()
    assert len(first) == len(second) == 2
    assert {row["report_id"] for row in first}.isdisjoint(row["report_id"] for row in second)


@pytest.mark.parametrize("query", ["status=invalid", "limit=0", "limit=201", "offset=-1", "offset=2147483648"])
def test_report_query_validation(reports_api, query):
    assert reports_api[0].get(f"/api/admin/reports?{query}", headers=headers()).status_code == 422


@pytest.mark.parametrize("body", [{"decision": "pending"}, {"decision": "resolved", "reviewer_id": uid(2)}])
def test_report_resolution_validation(reports_api, body):
    assert reports_api[0].patch(f"/api/admin/reports/{uid(6001)}/resolve", json=body, headers=headers()).status_code == 422


def test_dismiss_keeps_content_and_only_closes_selected_report(reports_api):
    client, engine, _ = reports_api
    response = client.patch(f"/api/admin/reports/{uid(6001)}/resolve", json={"decision": "dismissed"}, headers=headers())
    assert response.status_code == 200, response.text
    assert response.json() == {"report_id": uid(6001), "status": "dismissed", "deleted_target_count": 0, "resolved_report_count": 0}
    assert scalar(engine, "SELECT COUNT(*) FROM community.Posts WHERE Id=:id", id=uid(5001)) == 1
    assert scalar(engine, "SELECT Status FROM community.ReportedContents WHERE Id=:id", id=uid(6002)) == "pending"
    history = client.get("/api/admin/reports?status=dismissed", headers=headers()).json()
    assert [row["report_id"] for row in history] == [uid(6001)]


@pytest.mark.parametrize("report,target,table,count", [(6001, 5001, "Posts", 4), (6003, 5101, "Comments", 1), (6004, 5201, "PostMedia", 1)])
def test_resolve_deletes_content_closes_related_reports_and_audits(reports_api, report, target, table, count):
    client, engine, _ = reports_api
    response = client.patch(f"/api/admin/reports/{uid(report)}/resolve", json={"decision": "resolved"}, headers=headers())
    assert response.status_code == 200, response.text
    assert response.json()["deleted_target_count"] == 1
    assert response.json()["resolved_report_count"] == count
    assert scalar(engine, f"SELECT COUNT(*) FROM community.{table} WHERE Id=:id", id=uid(target)) == 0
    assert scalar(engine, "SELECT COUNT(*) FROM community.ReportedContents WHERE Status='resolved'") == count
    assert scalar(engine, "SELECT COUNT(*) FROM reports.AuditLog WHERE Action LIKE 'report.resolved%' AND UserId=:id", id=uid(1)) == 1
    assert client.patch(f"/api/admin/reports/{uid(report)}/resolve", json={"decision": "resolved"}, headers=headers()).status_code == 409
    if table == "Posts":
        assert scalar(engine, "SELECT COUNT(*) FROM community.Comments WHERE PostId=:id", id=uid(target)) == 0
        assert scalar(engine, "SELECT COUNT(*) FROM community.PostMedia WHERE PostId=:id", id=uid(target)) == 0
        rows = client.get("/api/admin/statistics", headers=headers()).json()
        assert next(row for row in rows if row["family_id"] == uid(1001))["post_count"] == 1


@pytest.mark.parametrize("report", [6006, 6007, 9999])
def test_missing_or_unsupported_target_returns_404_without_changes(reports_api, report):
    response = reports_api[0].patch(f"/api/admin/reports/{uid(report)}/resolve", json={"decision": "resolved"}, headers=headers())
    assert response.status_code == 404, response.text
    assert scalar(reports_api[1], "SELECT COUNT(*) FROM community.ReportedContents WHERE Status='pending'") == 7


def test_audit_failure_rolls_back_content_and_all_report_statuses(reports_api):
    client, engine, options = reports_api
    options["fail_audit"] = True
    response = client.patch(f"/api/admin/reports/{uid(6001)}/resolve", json={"decision": "resolved"}, headers=headers())
    assert response.status_code == 500, response.text
    assert "Injected" not in response.text and "FC_SQL" not in response.text
    assert scalar(engine, "SELECT COUNT(*) FROM community.Posts WHERE Id=:id", id=uid(5001)) == 1
    assert scalar(engine, "SELECT COUNT(*) FROM community.Comments WHERE Id=:id", id=uid(5101)) == 1
    assert scalar(engine, "SELECT COUNT(*) FROM community.PostMedia WHERE Id=:id", id=uid(5201)) == 1
    assert scalar(engine, "SELECT COUNT(*) FROM community.ReportedContents WHERE Status='pending'") == 7


@pytest.mark.parametrize("has_ai", [False, True])
@pytest.mark.parametrize("fail_audit", [False, True])
def test_post_resolution_with_optional_ai_storage(reports_api, has_ai, fail_audit):
    client, engine, options = reports_api
    options["fail_audit"] = fail_audit
    try:
        with engine.begin() as connection:
            if has_ai:
                connection.execute(text("""
                    INSERT heritage.KnowledgeChunks (FamilyId, SourceType, SourceId, ChunkIndex, ChunkText)
                    VALUES (:family, N'post', :post, 0, N'Chunk 1'),
                           (:family, N'post', :post, 1, N'Chunk 2'),
                           (:family, N'post', :other, 0, N'Keep other post'),
                           (:family, N'member', :post, 0, N'Keep other source type')
                """), {"family": uid(1001), "post": uid(5001), "other": uid(5002)})
            else:
                connection.exec_driver_sql("DROP TABLE heritage.KnowledgeChunks").close()
                # Deploy the procedure before AI is installed, not only with a warmed query plan.
                execute_script(connection, (ROOT / "database/procedures/01_core_procs.sql").read_text(encoding="utf-8-sig"),
                               engine.url.database)

        response = client.patch(f"/api/admin/reports/{uid(6001)}/resolve",
                                json={"decision": "resolved"}, headers=headers())
        assert response.status_code == (500 if fail_audit else 200), response.text
        assert scalar(engine, "SELECT COUNT(*) FROM community.Posts WHERE Id=:id", id=uid(5001)) == int(fail_audit)
        assert scalar(engine, "SELECT COUNT(*) FROM community.ReportedContents WHERE Status='resolved'") == (0 if fail_audit else 4)
        assert scalar(engine, "SELECT COUNT(*) FROM reports.AuditLog WHERE Action LIKE 'report.resolved%'") == int(not fail_audit)
        if has_ai:
            assert scalar(engine, "SELECT COUNT(*) FROM heritage.KnowledgeChunks WHERE SourceType='post' AND SourceId=:id",
                          id=uid(5001)) == (2 if fail_audit else 0)
            assert scalar(engine, "SELECT COUNT(*) FROM heritage.KnowledgeChunks WHERE SourceType='post' AND SourceId=:id",
                          id=uid(5002)) == 1
            assert scalar(engine, "SELECT COUNT(*) FROM heritage.KnowledgeChunks WHERE SourceType='member' AND SourceId=:id",
                          id=uid(5001)) == 1
        else:
            assert scalar(engine, "SELECT OBJECT_ID(N'heritage.KnowledgeChunks', N'U')") is None
    finally:
        with engine.begin() as connection:
            if has_ai:
                connection.exec_driver_sql("DELETE heritage.KnowledgeChunks").close()
            else:
                execute_script(connection, (ROOT / "database/schema/07_ai_assistant.sql").read_text(encoding="utf-8-sig"),
                               engine.url.database)


def test_report_escalation_handles_multirow_insert_without_duplicate_audit(reports_api):
    _, engine, _ = reports_api
    insert = text("""INSERT community.ReportedContents (TargetId, TargetType, ReportedBy, Reason)
                     VALUES (:target, N'post', :user, N'Threshold test')""")
    with engine.begin() as connection:
        connection.execute(text("""INSERT community.ReportedContents (TargetId, TargetType, ReportedBy, Reason)
                                   VALUES (:target, N'post', :first, N'Threshold test'),
                                          (:target, N'post', :second, N'Threshold test')"""),
                           {"target": uid(5001), "first": uid(3), "second": uid(8)})
    assert scalar(engine, "SELECT COUNT(*) FROM reports.AuditLog WHERE Action LIKE 'ESCALATE:%'") == 1
    with engine.begin() as connection:
        connection.execute(insert, {"target": uid(5001), "user": uid(3)})
    assert scalar(engine, "SELECT COUNT(*) FROM reports.AuditLog WHERE Action LIKE 'ESCALATE:%'") == 1
