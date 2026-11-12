"""Truy vấn CSDL cho domain community.

Mọi thao tác ghi quan trọng đều đi qua Stored Procedure của phân hệ
Cộng đồng & Sự kiện (database/procedures/03_community_procs.sql) thay vì
tự dựng câu lệnh INSERT/UPDATE ở tầng ứng dụng.
"""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def create_post_with_media(
    db: Session,
    *,
    user_id: UUID,
    family_id: UUID,
    content: str,
    media_json: str | None,
) -> UUID:
    """Gọi community.usp_CreatePostWithMedia. Bài viết và ảnh nằm trong một giao tác."""
    stmt = text(
        """
        DECLARE @NewPostId UNIQUEIDENTIFIER;
        EXEC community.usp_CreatePostWithMedia
            @UserId    = :user_id,
            @FamilyId  = :family_id,
            @Content   = :content,
            @MediaJson = :media_json,
            @PostId    = @NewPostId OUTPUT;
        SELECT @NewPostId AS PostId;
        """
    )
    row = (
        db.execute(
            stmt,
            {
                "user_id": str(user_id),
                "family_id": str(family_id),
                "content": content,
                "media_json": media_json,
            },
        )
        .mappings()
        .one()
    )
    db.commit()
    return UUID(str(row["PostId"]))


def list_newsfeed(
    db: Session,
    *,
    family_id: UUID,
    offset: int,
    limit: int,
) -> list[Mapping[str, Any]]:
    """Đọc bảng tin từ View community.vw_NewsfeedPosts, mới nhất trước."""
    stmt = text(
        """
        SELECT PostId, FamilyId, AuthorId, AuthorName, Content, CreatedAt,
               CommentCount, ReactionCount, MediaUrls
        FROM community.vw_NewsfeedPosts
        WHERE FamilyId = :family_id
        ORDER BY CreatedAt DESC
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """
    )
    return list(
        db.execute(stmt, {"family_id": str(family_id), "offset": offset, "limit": limit})
        .mappings()
        .all()
    )


def count_newsfeed(db: Session, *, family_id: UUID) -> int:
    stmt = text("SELECT COUNT_BIG(*) FROM community.Posts WHERE FamilyId = :family_id")
    return int(db.execute(stmt, {"family_id": str(family_id)}).scalar() or 0)


def get_post(db: Session, *, post_id: UUID) -> Mapping[str, Any] | None:
    stmt = text(
        """
        SELECT PostId, FamilyId, AuthorId, AuthorName, Content, CreatedAt,
               CommentCount, ReactionCount, MediaUrls
        FROM community.vw_NewsfeedPosts
        WHERE PostId = :post_id
        """
    )
    return db.execute(stmt, {"post_id": str(post_id)}).mappings().one_or_none()


def add_comment(db: Session, *, post_id: UUID, user_id: UUID, content: str) -> Mapping[str, Any]:
    """Bảng Comments không có SP riêng nên chèn trực tiếp, có OUTPUT để lấy lại dòng vừa tạo."""
    stmt = text(
        """
        INSERT INTO community.Comments (PostId, UserId, Content)
        OUTPUT inserted.Id, inserted.PostId, inserted.UserId, inserted.Content, inserted.CreatedAt
        VALUES (:post_id, :user_id, :content)
        """
    )
    row = (
        db.execute(stmt, {"post_id": str(post_id), "user_id": str(user_id), "content": content})
        .mappings()
        .one()
    )
    db.commit()
    return row


def list_comments(db: Session, *, post_id: UUID, offset: int, limit: int) -> list[Mapping[str, Any]]:
    stmt = text(
        """
        SELECT c.Id, c.PostId, c.UserId, u.FullName AS AuthorName, c.Content, c.CreatedAt
        FROM community.Comments AS c
        LEFT JOIN core.Users AS u ON u.UserId = c.UserId
        WHERE c.PostId = :post_id
        ORDER BY c.CreatedAt
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """
    )
    return list(
        db.execute(stmt, {"post_id": str(post_id), "offset": offset, "limit": limit}).mappings().all()
    )


def upsert_reaction(db: Session, *, post_id: UUID, user_id: UUID, reaction_type: str | None) -> None:
    """Gọi community.usp_UpsertReaction (MERGE). reaction_type = None thì gỡ cảm xúc."""
    stmt = text(
        """
        EXEC community.usp_UpsertReaction
            @PostId = :post_id,
            @UserId = :user_id,
            @Type   = :reaction_type
        """
    )
    db.execute(
        stmt,
        {"post_id": str(post_id), "user_id": str(user_id), "reaction_type": reaction_type},
    )
    db.commit()


def count_reactions(db: Session, *, post_id: UUID) -> int:
    stmt = text("SELECT COUNT_BIG(*) FROM community.Reactions WHERE PostId = :post_id")
    return int(db.execute(stmt, {"post_id": str(post_id)}).scalar() or 0)


def create_report(
    db: Session,
    *,
    target_id: UUID,
    target_type: str,
    reported_by: UUID,
    reason: str,
) -> Mapping[str, Any]:
    """Chèn báo cáo. Trigger trg_ReportedContents_Escalation sẽ tự ghi AuditLog khi đủ ngưỡng."""
    stmt = text(
        """
        INSERT INTO community.ReportedContents (TargetId, TargetType, ReportedBy, Reason)
        OUTPUT inserted.Id, inserted.TargetId, inserted.TargetType, inserted.Status, inserted.CreatedAt
        VALUES (:target_id, :target_type, :reported_by, :reason)
        """
    )
    row = (
        db.execute(
            stmt,
            {
                "target_id": str(target_id),
                "target_type": target_type,
                "reported_by": str(reported_by),
                "reason": reason,
            },
        )
        .mappings()
        .one()
    )
    db.commit()
    return row
