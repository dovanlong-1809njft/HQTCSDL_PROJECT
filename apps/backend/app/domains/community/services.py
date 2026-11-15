"""Nghiệp vụ phân hệ Cộng đồng: đăng bài kèm ảnh, bình luận, cảm xúc, báo cáo."""

import json
from uuid import UUID

from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.family_access import require_family_access
from app.domains.identity.models import User
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
        media_urls=[item["url"] for item in json.loads(row["MediaJson"] or "[]")] if row.get("MediaJson") is not None else _split_media(row["MediaUrls"]),
        is_announcement=bool(row.get("IsAnnouncement",False)),
        my_reaction=row.get("MyReaction"),
    )


def create_post_service(payload: PostCreateRequest, actor: User, db: Session) -> PostResponse:
    require_family_access(db, actor, payload.family_id,manage=payload.is_announcement)
    media_json = (
        json.dumps([item.model_dump() for item in payload.media], ensure_ascii=False)
        if payload.media
        else None
    )
    try:
        post_id = repository.create_post_with_media(
            db,
            user_id=actor.id,
            family_id=payload.family_id,
            content=payload.content,
            media_json=media_json,
            is_announcement=payload.is_announcement,
        )
    except DBAPIError as exc:  # SP ném THROW 50701/50702/50703 khi dữ liệu không hợp lệ
        db.rollback()
        raise NotFoundError("Không tạo được bài viết: người dùng hoặc gia đình không tồn tại.") from exc

    row = repository.get_post(db, post_id=post_id,actor_id=actor.id)
    if row is None:
        raise NotFoundError("Bài viết vừa tạo không đọc lại được.")
    return _to_post_response(row)


def list_newsfeed_service(
    family_id: UUID, page: PageParams, actor: User, db: Session
) -> PaginatedResponse[PostResponse]:
    require_family_access(db, actor, family_id)
    rows = repository.list_newsfeed(
        db, family_id=family_id, offset=page.offset, limit=page.page_size,actor_id=actor.id
    )
    return PaginatedResponse[PostResponse](
        items=[_to_post_response(row) for row in rows],
        total=repository.count_newsfeed(db, family_id=family_id),
        page=page.page,
        page_size=page.page_size,
    )


def _accessible_post(post_id: UUID, actor: User, db: Session):
    row = repository.get_post(db, post_id=post_id,actor_id=actor.id)
    if row is None:
        raise NotFoundError("Bài viết không tồn tại.")
    require_family_access(db, actor, row["FamilyId"])
    return row


def get_post_service(post_id: UUID, actor: User, db: Session) -> PostResponse:
    return _to_post_response(_accessible_post(post_id, actor, db))


def add_comment_service(
    post_id: UUID, payload: CommentCreateRequest, actor: User, db: Session
) -> CommentResponse:
    _accessible_post(post_id, actor, db)
    row = repository.add_comment(
        db, post_id=post_id, user_id=actor.id, content=payload.content.strip()
    )
    return CommentResponse(
        id=row["Id"],
        post_id=row["PostId"],
        user_id=row["UserId"],
        content=row["Content"],
        created_at=row["CreatedAt"],
    )


def list_comments_service(post_id: UUID, page: PageParams, actor: User, db: Session) -> list[CommentResponse]:
    _accessible_post(post_id, actor, db)
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
    post_id: UUID, payload: ReactionRequest, actor: User, db: Session
) -> ReactionResponse:
    _accessible_post(post_id, actor, db)
    try:
        repository.upsert_reaction(
            db, post_id=post_id, user_id=actor.id, reaction_type=payload.type
        )
    except DBAPIError as exc:  # THROW 50711 khi bài viết không tồn tại, CHECK khi sai loại cảm xúc
        db.rollback()
        raise NotFoundError("Không ghi được cảm xúc: bài viết không tồn tại hoặc loại không hợp lệ.") from exc

    return ReactionResponse(
        post_id=post_id,
        user_id=actor.id,
        type=payload.type,
        reaction_count=repository.count_reactions(db, post_id=post_id),
    )


def create_report_service(
    payload: ReportCreateRequest, actor: User, db: Session
) -> ReportResponse:
    family_id = repository.get_report_family(db, payload.target_type, payload.target_id)
    if family_id is None:
        raise NotFoundError("Nội dung bị báo cáo không tồn tại.")
    require_family_access(db, actor, family_id)
    row = repository.create_report(
        db,
        target_id=payload.target_id,
        target_type=payload.target_type,
        reported_by=actor.id,
        reason=payload.reason.strip(),
    )
    return ReportResponse(
        id=row["Id"],
        target_id=row["TargetId"],
        target_type=row["TargetType"],
        status=row["Status"],
        created_at=row["CreatedAt"],
    )
