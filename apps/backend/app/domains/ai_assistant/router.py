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
    RelationshipExplainRequest,
    RelationshipExplainResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SyncPendingRequest,
    SyncPendingResponse,
    UpsertChunkRequest,
    UpsertChunkResponse,
)
from app.domains.ai_assistant.services import (
    chunk_and_index_source_service,
    embed_and_upsert_chunk_service,
    explain_relationship_service,
    semantic_search_service,
    sync_pending_knowledge_service,
    test_embedding_service,
    test_sql_cosine_service,
)
from app.domains.identity.models import User

router = APIRouter(prefix="/ai", tags=["ai-assistant"])
Admin = Annotated[User, Depends(require_role("admin"))]
Manager = Annotated[User, Depends(require_role("admin", "family_head"))]


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
    db: Annotated[Session, Depends(get_db)],
) -> ChunkAndIndexResponse:
    """
    Tuần 2 - Pipeline Cắt đoạn (Chunking):
    Tự động cắt văn bản bài viết/di sản thành các đoạn ngắn 3-4 câu,
    gọi Gemini lấy Vector và thực thi usp_UpsertKnowledgeChunk lưu vào SQL Server.
    """
    return chunk_and_index_source_service(payload, db)


@router.post("/sync-pending", response_model=SyncPendingResponse)
def sync_pending_knowledge(
    payload: SyncPendingRequest,
    db: Annotated[Session, Depends(get_db)],
) -> SyncPendingResponse:
    """
    Tuần 2 - Đồng bộ tự động:
    Quét toàn bộ bài viết (community.Posts của TV3) và tư liệu di sản (heritage.Items của TV4)
    chưa có Vector hoặc đang 'pending', tự động cắt đoạn 3-4 câu, lấy Vector Gemini và lưu vào CSDL.
    """
    return sync_pending_knowledge_service(payload, db)


@router.post("/semantic-search", response_model=SemanticSearchResponse)
def semantic_search(
    payload: SemanticSearchRequest,
    db: Annotated[Session, Depends(get_db)],
) -> SemanticSearchResponse:
    """
    Tuần 2 - API Semantic Search & RAG:
    Nhận câu hỏi tìm kiếm của người dùng, chuyển thành Vector và gọi usp_SemanticSearch
    để lấy Top-K đoạn văn bản tương đồng cao nhất (kèm câu trả lời tổng hợp từ Gemini).
    """
    return semantic_search_service(payload, db)


@router.post("/explain-relationship", response_model=RelationshipExplainResponse)
def explain_relationship(
    payload: RelationshipExplainRequest,
    db: Annotated[Session, Depends(get_db)],
) -> RelationshipExplainResponse:
    """
    Tuần 2 - Giải thích quan hệ họ hàng (Prompt Engineering):
    Truy vấn usp_FindRelationshipPath trên bảng bao đóng MemberClosure của TV2,
    ghép dữ liệu vào Prompt Template và gọi Gemini sinh lời giải thích tự nhiên.
    """
    return explain_relationship_service(payload, db)
