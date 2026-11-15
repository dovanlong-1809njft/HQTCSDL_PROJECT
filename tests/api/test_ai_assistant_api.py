"""Kiểm thử Unit & API phân hệ Trợ lý ảo AI (TV5) — Tuần 1 & Tuần 2."""

from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[2] / "apps" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import get_db
from app.domains.ai_assistant import services
from app.main import app

FAMILY_ID = UUID("22222222-2222-2222-2222-000000000001")
USER_ID = UUID("11111111-1111-1111-1111-000000000001")
SOURCE_ID = UUID("eeeeeeee-eeee-eeee-eeee-000000000003")
MEMBER_A = UUID("44444444-4444-4444-4444-000000000001")
MEMBER_B = UUID("44444444-4444-4444-4444-000000000005")


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


class FakeAiSession:
    def __init__(self) -> None:
        self.statements: list[tuple[str, dict]] = []
        self.commits = 0
        self.rollbacks = 0

    def execute(self, statement, params=None):
        sql = " ".join(str(statement).split())
        self.statements.append((sql, params or {}))

        if "heritage.fn_CosineSimilarity" in sql:
            return FakeResult(scalar=0.9125)
        if "usp_UpsertKnowledgeChunk" in sql:
            return FakeResult([{"ChunkId": str(uuid4()), "ActionTaken": "INSERT"}])
        if "usp_ClearStaleKnowledgeChunks" in sql:
            return FakeResult([{"DeletedChunkCount": 0}])
        if "vw_PendingKnowledgeSources" in sql:
            return FakeResult(
                [
                    {
                        "FamilyId": FAMILY_ID,
                        "SourceType": "heritage",
                        "SourceId": SOURCE_ID,
                        "Title": "Chuyện cụ Cẩn dựng nhà thờ họ",
                        "RawContent": "Câu một. Câu hai. Câu ba. Câu bốn. Câu năm.",
                        "SyncStatus": "unindexed",
                        "CreatedAt": datetime.now(timezone.utc),
                    }
                ]
            )
        if "usp_SemanticSearch" in sql:
            return FakeResult(
                [
                    {
                        "ChunkId": uuid4(),
                        "FamilyId": FAMILY_ID,
                        "SourceType": "heritage",
                        "SourceId": SOURCE_ID,
                        "SourceTitle": "Nghề mộc truyền trong họ",
                        "ChunkIndex": 0,
                        "ChunkText": "Nghề mộc theo họ Nguyễn Văn từ đời cụ tổ ở Thạch Thất.",
                        "SummaryText": "Ghi chép nghề mộc 3 đời.",
                        "SimilarityScore": 0.8942,
                        "UpdatedAt": datetime.now(timezone.utc),
                    }
                ]
            )
        if "usp_FindRelationshipPath" in sql:
            return FakeResult(
                [
                    {
                        "MemberAId": MEMBER_A,
                        "MemberAName": "Nguyễn Văn Cẩn",
                        "MemberABirthDate": date(1938, 3, 12),
                        "MemberABranchName": "Chi trưởng",
                        "MemberBId": MEMBER_B,
                        "MemberBName": "Nguyễn Văn Hùng",
                        "MemberBBirthDate": date(1995, 9, 24),
                        "MemberBBranchName": "Chi thứ",
                        "RelationshipCategory": "direct_lineage",
                        "CommonAncestorId": MEMBER_A,
                        "CommonAncestorName": "Nguyễn Văn Cẩn",
                        "DepthFromAncestorToA": 0,
                        "DepthFromAncestorToB": 2,
                        "TotalGenerationDistance": 2,
                        "PathFromAncestorToA": "Nguyễn Văn Cẩn",
                        "PathFromAncestorToB": "Nguyễn Văn Cẩn -> Nguyễn Văn Trường -> Nguyễn Văn Hùng",
                        "SuggestedKinship": "Trực hệ: A là Ông/Bà (nội/ngoại) của B (B gọi A là Ông/Bà, xưng Cháu)",
                    }
                ]
            )
        if "usp_SaveAiChatMessage" in sql:
            return FakeResult([{"MessageId": str(uuid4()), "CreatedAt": datetime.now(timezone.utc)}])

        return FakeResult()

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


@pytest.fixture
def ai_client(monkeypatch: pytest.MonkeyPatch):
    fake_db = FakeAiSession()
    app.dependency_overrides[get_db] = lambda: fake_db

    monkeypatch.setattr(
        services,
        "generate_embeddings_batch",
        lambda texts: [[0.5, 0.5, 0.5] for _ in texts],
    )
    monkeypatch.setattr(
        services,
        "generate_gemini_answer",
        lambda prompt: "Câu trả lời tự nhiên từ Gemini dựa trên dữ liệu SQL.",
    )

    with TestClient(app) as client:
        yield client, fake_db
    app.dependency_overrides.clear()


def test_split_text_into_sentence_chunks_groups_by_3_sentences():
    text_input = (
        "Câu thứ nhất về cụ tổ. Câu thứ hai về nhà thờ họ! "
        "Câu thứ ba về giỗ tổ? Câu thứ tư về nghề mộc. Câu thứ năm về con cháu."
    )
    chunks = services.split_text_into_sentence_chunks(
        text_input,
        sentences_per_chunk=3,
        title="Gia phả họ Nguyễn",
    )
    assert len(chunks) == 2
    assert chunks[0].startswith("[Gia phả họ Nguyễn]")
    assert "Câu thứ nhất" in chunks[0] and "Câu thứ ba" in chunks[0]
    assert "Câu thứ tư" in chunks[1] and "Câu thứ năm" in chunks[1]


def test_chunk_and_index_endpoint(ai_client):
    client, fake_db = ai_client
    res = client.post(
        "/api/ai/chunk-and-index",
        json={
            "family_id": str(FAMILY_ID),
            "source_type": "heritage",
            "source_id": str(SOURCE_ID),
            "title": "Chuyện cụ Cẩn dựng nhà thờ họ",
            "content": "Câu 1. Câu 2. Câu 3. Câu 4. Câu 5.",
            "sentences_per_chunk": 3,
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["total_chunks"] == 2
    assert len(body["chunks"]) == 2
    assert fake_db.commits >= 1


def test_sync_pending_endpoint(ai_client):
    client, _ = ai_client
    res = client.post(
        "/api/ai/sync-pending",
        json={"family_id": str(FAMILY_ID), "sentences_per_chunk": 3, "limit": 10},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["sources_processed"] == 1
    assert body["total_chunks_upserted"] == 2


def test_semantic_search_endpoint(ai_client):
    client, _ = ai_client
    res = client.post(
        "/api/ai/semantic-search",
        json={
            "family_id": str(FAMILY_ID),
            "query": "Dòng họ mình có nghề truyền thống gì?",
            "top_k": 3,
            "min_score": 0.3,
            "generate_answer": True,
            "user_id": str(USER_ID),
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["total_matches"] == 1
    assert body["matches"][0]["similarity_score"] == pytest.approx(0.8942)
    assert body["ai_answer"] is not None
    assert "Dòng họ mình có nghề truyền thống gì?" in body["prompt_used"]


def test_explain_relationship_endpoint(ai_client):
    client, _ = ai_client
    res = client.post(
        "/api/ai/explain-relationship",
        json={
            "family_id": str(FAMILY_ID),
            "member_a_id": str(MEMBER_A),
            "member_b_id": str(MEMBER_B),
            "question": "Cụ Cẩn và Hùng xưng hô thế nào?",
            "user_id": str(USER_ID),
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["relationship_path"]["common_ancestor_name"] == "Nguyễn Văn Cẩn"
    assert body["relationship_path"]["depth_from_ancestor_to_b"] == 2
    assert body["ai_explanation"] is not None
    assert "Nguyễn Văn Cẩn -> Nguyễn Văn Trường -> Nguyễn Văn Hùng" in body["prompt_used"]
