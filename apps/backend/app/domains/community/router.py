"""API phân hệ Cộng đồng: bảng tin, bình luận, cảm xúc và báo cáo nội dung."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.domains.community.schemas import (
    CommentCreateRequest,
    CommentResponse,
    PostCreateRequest,
    PostResponse,
    ReactionRequest,
    ReactionResponse,
    ReportCreateRequest,
    ReportResponse,
)
from app.domains.community.services import (
    add_comment_service,
    create_post_service,
    create_report_service,
    get_post_service,
    list_comments_service,
    list_newsfeed_service,
    upsert_reaction_service,
)
from app.domains.identity.models import User
from app.shared.pagination import PageParams, PaginatedResponse

router = APIRouter(prefix="/community", tags=["community"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreateRequest, current_user: CurrentUser, db: DbSession) -> PostResponse:
    """Đăng bài kèm ảnh. Bài viết và danh sách ảnh ghi trong một giao tác (usp_CreatePostWithMedia)."""
    return create_post_service(payload, current_user.id, db)


@router.get("/posts", response_model=PaginatedResponse[PostResponse])
def list_posts(
    family_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[PostResponse]:
    """Bảng tin của một gia đình, đọc từ View vw_NewsfeedPosts."""
    return list_newsfeed_service(family_id, PageParams(page=page, page_size=page_size), db)


@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: UUID, current_user: CurrentUser, db: DbSession) -> PostResponse:
    return get_post_service(post_id, db)


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    post_id: UUID, payload: CommentCreateRequest, current_user: CurrentUser, db: DbSession
) -> CommentResponse:
    return add_comment_service(post_id, payload, current_user.id, db)


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
def list_comments(
    post_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[CommentResponse]:
    return list_comments_service(post_id, PageParams(page=page, page_size=page_size), db)


@router.put("/posts/{post_id}/reactions", response_model=ReactionResponse)
def upsert_reaction(
    post_id: UUID, payload: ReactionRequest, current_user: CurrentUser, db: DbSession
) -> ReactionResponse:
    """Thả hoặc đổi cảm xúc (MERGE). Gửi type = null để gỡ cảm xúc."""
    return upsert_reaction_service(post_id, payload, current_user.id, db)


@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: ReportCreateRequest, current_user: CurrentUser, db: DbSession
) -> ReportResponse:
    """Báo cáo nội dung. Đủ 3 báo cáo thì Trigger tự ghi cảnh báo vào reports.AuditLog."""
    return create_report_service(payload, current_user.id, db)
