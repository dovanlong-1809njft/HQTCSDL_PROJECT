"""Nghiệp vụ phân hệ Cộng đồng: đăng bài kèm ảnh, bình luận, cảm xúc, báo cáo."""

import json
from uuid import UUID

from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domains.community import repository
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
from app.shared.pagination import PageParams, PaginatedResponse


def _split_media(media_urls: str | None) -> list[str]:
    """View trả về các MediaUrl nối bằng dấu phẩy (STRING_AGG)."""
    if not media_urls:
        return []
    return [url for url in (part.strip() for part in media_urls.split(",")) if url]


def _to_post_response(row) -> PostResponse:
    return PostResponse(
        post_id=row["PostId"],
        family_id=row["FamilyId"],
        author_id=row["AuthorId"],
        author_name=row["AuthorName"],
        content=row["Content"],
        created_at=row["CreatedAt"],
        comment_count=int(row["CommentCount"] or 0),
        reaction_count=int(row["ReactionCount"] or 0),
        media_urls=_split_media(row["MediaUrls"]),
    )


def create_post_service(payload: PostCreateRequest, user_id: UUID, db: Session) -> PostResponse:
    media_json = (
        json.dumps([item.model_dump() for item in payload.media], ensure_ascii=False)
        if payload.media
        else None
    )
    try:
        post_id = repository.create_post_with_media(
            db,
            user_id=user_id,
            family_id=payload.family_id,
            content=payload.content,
            media_json=media_json,
        )
    except DBAPIError as exc:  # SP ném THROW 50701/50702/50703 khi dữ liệu không hợp lệ
        db.rollback()
        raise NotFoundError("Không tạo được bài viết: người dùng hoặc gia đình không tồn tại.") from exc

    row = repository.get_post(db, post_id=post_id)
    if row is None:
        raise NotFoundError("Bài viết vừa tạo không đọc lại được.")
    return _to_post_response(row)


def list_newsfeed_service(
    family_id: UUID, page: PageParams, db: Session
) -> PaginatedResponse[PostResponse]:
    rows = repository.list_newsfeed(
        db, family_id=family_id, offset=page.offset, limit=page.page_size
    )
    return PaginatedResponse[PostResponse](
        items=[_to_post_response(row) for row in rows],
        total=repository.count_newsfeed(db, family_id=family_id),
        page=page.page,
        page_size=page.page_size,
    )


def get_post_service(post_id: UUID, db: Session) -> PostResponse:
    row = repository.get_post(db, post_id=post_id)
    if row is None:
        raise NotFoundError("Bài viết không tồn tại.")
    return _to_post_response(row)


def add_comment_service(
    post_id: UUID, payload: CommentCreateRequest, user_id: UUID, db: Session
) -> CommentResponse:
    if repository.get_post(db, post_id=post_id) is None:
        raise NotFoundError("Bài viết không tồn tại.")
    row = repository.add_comment(
        db, post_id=post_id, user_id=user_id, content=payload.content.strip()
    )
    return CommentResponse(
        id=row["Id"],
        post_id=row["PostId"],
        user_id=row["UserId"],
        content=row["Content"],
        created_at=row["CreatedAt"],
    )


def list_comments_service(post_id: UUID, page: PageParams, db: Session) -> list[CommentResponse]:
    rows = repository.list_comments(db, post_id=post_id, offset=page.offset, limit=page.page_size)
    return [
        CommentResponse(
            id=row["Id"],
            post_id=row["PostId"],
            user_id=row["UserId"],
            author_name=row["AuthorName"],
            content=row["Content"],
            created_at=row["CreatedAt"],
        )
        for row in rows
    ]


def upsert_reaction_service(
    post_id: UUID, payload: ReactionRequest, user_id: UUID, db: Session
) -> ReactionResponse:
    try:
        repository.upsert_reaction(
            db, post_id=post_id, user_id=user_id, reaction_type=payload.type
        )
    except DBAPIError as exc:  # THROW 50711 khi bài viết không tồn tại, CHECK khi sai loại cảm xúc
        db.rollback()
        raise NotFoundError("Không ghi được cảm xúc: bài viết không tồn tại hoặc loại không hợp lệ.") from exc

    return ReactionResponse(
        post_id=post_id,
        user_id=user_id,
        type=payload.type,
        reaction_count=repository.count_reactions(db, post_id=post_id),
    )


def create_report_service(
    payload: ReportCreateRequest, user_id: UUID, db: Session
) -> ReportResponse:
    row = repository.create_report(
        db,
        target_id=payload.target_id,
        target_type=payload.target_type,
        reported_by=user_id,
        reason=payload.reason.strip(),
    )
    return ReportResponse(
        id=row["Id"],
        target_id=row["TargetId"],
        target_type=row["TargetType"],
        status=row["Status"],
        created_at=row["CreatedAt"],
    )
