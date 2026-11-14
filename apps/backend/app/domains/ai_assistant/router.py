from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.domains.identity.models import User
from app.domains.ai_assistant.schemas import (
    CosineTestRequest,
    CosineTestResponse,
    EmbeddingTestRequest,
    EmbeddingTestResponse,
    UpsertChunkRequest,
    UpsertChunkResponse,
)
from app.domains.ai_assistant.services import (
    embed_and_upsert_chunk_service,
    test_embedding_service,
    test_sql_cosine_service,
)

router = APIRouter(prefix="/ai", tags=["ai-assistant"])
Admin = Annotated[User, Depends(require_role("admin"))]
Manager = Annotated[User, Depends(require_role("admin", "family_head"))]


@router.post("/test-embedding", response_model=EmbeddingTestResponse)
def test_embedding(payload: EmbeddingTestRequest, current_user: Admin) -> EmbeddingTestResponse:
    """Dummy API (Tuần 1): Kiểm tra kết nối Gemini SDK và lấy Vector nhúng về."""
    return test_embedding_service(payload.text)


@router.post("/test-cosine", response_model=CosineTestResponse)
def test_cosine(
    payload: CosineTestRequest,
    current_user: Admin,
    db: Annotated[Session, Depends(get_db)],
) -> CosineTestResponse:
    """Kiểm tra tích hợp Gemini Vector + hàm T-SQL heritage.fn_CosineSimilarity."""
    return test_sql_cosine_service(payload, db)


@router.post("/chunks", response_model=UpsertChunkResponse, status_code=status.HTTP_201_CREATED)
def upsert_chunk(
    payload: UpsertChunkRequest,
    current_user: Manager,
    db: Annotated[Session, Depends(get_db)],
) -> UpsertChunkResponse:
    """Tính Vector bằng Gemini và lưu vào bảng KnowledgeChunks qua SP usp_UpsertKnowledgeChunk."""
    return embed_and_upsert_chunk_service(payload, current_user, db)
