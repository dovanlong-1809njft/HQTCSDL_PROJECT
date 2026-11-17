from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.domains.ai_assistant.schemas import (
    ChunkAndIndexRequest,
    ChunkAndIndexResponse,
    CosineTestRequest,
    CosineTestResponse,
    EmbeddingTestRequest,
    EmbeddingTestResponse,
    RecommendationRequest,
    RecommendationResponse,
    RelationshipExplainRequest,
    RelationshipExplainResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SummarizeRequest,
    SummarizeResponse,
    SyncPendingRequest,
    SyncPendingResponse,
    UpsertChunkRequest,
    UpsertChunkResponse,
)
from app.domains.ai_assistant.services import (
    chunk_and_index_source_service,
    embed_and_upsert_chunk_service,
    explain_relationship_service,
    recommend_related_service,
    semantic_search_service,
    summarize_content_service,
    sync_pending_knowledge_service,
    test_embedding_service,
    test_sql_cosine_service,
)
from app.domains.identity.models import User

router = APIRouter(prefix="/ai", tags=["ai-assistant"])

Admin = Annotated[User, Depends(require_role("admin"))]
Manager = Annotated[User, Depends(require_role("admin", "family_head"))]
Reader = Annotated[User, Depends(require_role("admin", "family_head", "member"))]


@router.post("/test-embedding", response_model=EmbeddingTestResponse)
def test_embedding(payload: EmbeddingTestRequest, current_user: Admin) -> EmbeddingTestResponse:
    """Tuần 1: Kiểm tra kết nối Gemini SDK và lấy Vector nhúng về."""
    return test_embedding_service(payload.text)


@router.post("/test-cosine", response_model=CosineTestResponse)
def test_cosine(
    payload: CosineTestRequest,
    current_user: Admin,
    db: Annotated[Session, Depends(get_db)],
) -> CosineTestResponse:
    """Tuần 1: Kiểm tra tích hợp Gemini Vector + hàm T-SQL heritage.fn_CosineSimilarity."""
    return test_sql_cosine_service(payload, db)


@router.post("/chunks", response_model=UpsertChunkResponse, status_code=status.HTTP_201_CREATED)
def upsert_chunk(
    payload: UpsertChunkRequest,
    current_user: Manager,
    db: Annotated[Session, Depends(get_db)],
) -> UpsertChunkResponse:
    """Tuần 1: Tính Vector bằng Gemini và lưu 1 đoạn vào bảng KnowledgeChunks qua usp_UpsertKnowledgeChunk."""
    return embed_and_upsert_chunk_service(payload, current_user, db)


@router.post(
    "/chunk-and-index",
    response_model=ChunkAndIndexResponse,
    status_code=status.HTTP_201_CREATED,
)
def chunk_and_index(
    payload: ChunkAndIndexRequest,
    current_user: Manager,
    db: Annotated[Session, Depends(get_db)],
) -> ChunkAndIndexResponse:
    """Tuần 2: Cắt đoạn 3-4 câu, lấy Vector Gemini và lưu vào SQL Server."""
    return chunk_and_index_source_service(payload, db, actor=current_user)


@router.post("/sync-pending", response_model=SyncPendingResponse)
def sync_pending_knowledge(
    payload: SyncPendingRequest,
    current_user: Manager,
    db: Annotated[Session, Depends(get_db)],
) -> SyncPendingResponse:
    """Tuần 2: Quét và đồng bộ Vector cho bài viết/di sản đang ở trạng thái pending."""
    return sync_pending_knowledge_service(payload, db, actor=current_user)


@router.post("/semantic-search", response_model=SemanticSearchResponse)
def semantic_search(
    payload: SemanticSearchRequest,
    current_user: Reader,
    db: Annotated[Session, Depends(get_db)],
) -> SemanticSearchResponse:
    """Tuần 2: Tìm kiếm theo ngữ nghĩa bằng AI & Trợ lý kiến thức gia đình RAG."""
    return semantic_search_service(payload, db, actor=current_user)


@router.post("/explain-relationship", response_model=RelationshipExplainResponse)
def explain_relationship(
    payload: RelationshipExplainRequest,
    current_user: Reader,
    db: Annotated[Session, Depends(get_db)],
) -> RelationshipExplainResponse:
    """Tuần 2: Giải thích mối quan hệ họ hàng và cách xưng hô bằng AI."""
    return explain_relationship_service(payload, db, actor=current_user)


@router.post("/summarize", response_model=SummarizeResponse)
def summarize_content(
    payload: SummarizeRequest,
    current_user: Reader,
    db: Annotated[Session, Depends(get_db)],
) -> SummarizeResponse:
    """Tuần 2: Tóm tắt nội dung tư liệu di sản hoặc bài viết cộng đồng bằng AI."""
    return summarize_content_service(payload, db, actor=current_user)


@router.post("/recommendations", response_model=RecommendationResponse)
def recommend_related(
    payload: RecommendationRequest,
    current_user: Reader,
    db: Annotated[Session, Depends(get_db)],
) -> RecommendationResponse:
    """Tuần 2: AI đề xuất các thành viên và tài nguyên di sản/bài viết liên quan."""
    return recommend_related_service(payload, db, actor=current_user)