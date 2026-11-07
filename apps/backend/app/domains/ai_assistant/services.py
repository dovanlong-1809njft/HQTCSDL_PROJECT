import json
from uuid import UUID

from fastapi import HTTPException, status
from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from app.core.config import GEMINI_API_KEY, GEMINI_EMBEDDING_DIM, GEMINI_EMBEDDING_MODEL
from app.domains.ai_assistant.repository import compute_cosine_similarity, upsert_knowledge_chunk
from app.domains.ai_assistant.schemas import (
    CosineTestRequest,
    CosineTestResponse,
    EmbeddingTestResponse,
    UpsertChunkRequest,
    UpsertChunkResponse,
)


def get_gemini_client() -> genai.Client:
    if not GEMINI_API_KEY or GEMINI_API_KEY == "replace_with_your_gemini_api_key":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chưa cấu hình GEMINI_API_KEY trong file .env.",
        )
    return genai.Client(api_key=GEMINI_API_KEY)


def generate_embedding(text_content: str) -> list[float]:
    """Gọi Google Gemini API để chuyển đoạn văn bản thành mảng số thực (Vector)."""
    client = get_gemini_client()
    try:
        response = client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            contents=text_content.strip(),
            config=types.EmbedContentConfig(
                output_dimensionality=GEMINI_EMBEDDING_DIM,
            ),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Lỗi khi gọi Gemini Embedding API: {exc}",
        ) from exc

    if not response.embeddings or not response.embeddings[0].values:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini không trả về dữ liệu Vector.",
        )
    return [round(float(v), 6) for v in response.embeddings[0].values]


def test_embedding_service(text_content: str) -> EmbeddingTestResponse:
    vector = generate_embedding(text_content)
    return EmbeddingTestResponse(
        model=GEMINI_EMBEDDING_MODEL,
        dimensions=len(vector),
        preview_first_5=vector[:5],
        embedding_json=json.dumps(vector),
    )


def test_sql_cosine_service(payload: CosineTestRequest, db: Session) -> CosineTestResponse:
    vec_a = generate_embedding(payload.text_a)
    vec_b = generate_embedding(payload.text_b)
    score = compute_cosine_similarity(db, json.dumps(vec_a), json.dumps(vec_b))
    return CosineTestResponse(
        text_a=payload.text_a,
        text_b=payload.text_b,
        dimensions=len(vec_a),
        cosine_similarity=score,
    )


def embed_and_upsert_chunk_service(payload: UpsertChunkRequest, db: Session) -> UpsertChunkResponse:
    vector = generate_embedding(payload.chunk_text)
    saved = upsert_knowledge_chunk(
        db,
        family_id=payload.family_id,
        source_type=payload.source_type,
        source_id=payload.source_id,
        chunk_index=payload.chunk_index,
        chunk_text=payload.chunk_text,
        embedding_json=json.dumps(vector),
        summary_text=payload.summary_text,
    )
    return UpsertChunkResponse(
        chunk_id=UUID(saved["chunk_id"]),
        action_taken=saved["action_taken"],
        dimensions=len(vector),
    )
