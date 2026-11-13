from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import TextClause


def _procedure_sql(statement: str) -> TextClause:
    # Some mssql-python versions omit the native error number from exceptions.
    # Preserve ERROR_NUMBER in a stable marker; statement is an internal SQL
    # literal and every request value remains a bound parameter.
    return text(f"""
        BEGIN TRY
            {statement}
        END TRY
        BEGIN CATCH
            DECLARE @ApiError NVARCHAR(2048) = CONCAT(N'[FC_SQL:', ERROR_NUMBER(), N'] ', ERROR_MESSAGE());
            THROW 50000, @ApiError, 1;
        END CATCH
    """)


def list_configs(db: Session, *, limit: int, offset: int) -> list[Mapping[str, Any]]:
    return list(db.execute(text("""
        SELECT ConfigKey, ConfigValue, Description, UpdatedAt
        FROM core.SystemConfigs
        ORDER BY ConfigKey
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
    """), {"limit": limit, "offset": offset}).mappings().all())


def get_config(db: Session, config_key: str) -> Mapping[str, Any] | None:
    return db.execute(text("""
        SELECT ConfigKey, ConfigValue, Description, UpdatedAt
        FROM core.SystemConfigs WHERE ConfigKey = :config_key
    """), {"config_key": config_key}).mappings().one_or_none()


def create_config(db: Session, *, actor_id: UUID, config_key: str, config_value: str,
                  description: str | None) -> Mapping[str, Any]:
    return db.execute(_procedure_sql("""
        EXEC core.usp_CreateSystemConfig
            @ActorUserId = :actor_id, @ConfigKey = :config_key,
            @ConfigValue = :config_value, @Description = :description
    """), {"actor_id": str(actor_id), "config_key": config_key,
           "config_value": config_value, "description": description}).mappings().one()


def update_config(db: Session, *, actor_id: UUID, config_key: str, config_value: str,
                  description: str | None) -> Mapping[str, Any]:
    return db.execute(_procedure_sql("""
        EXEC core.usp_UpdateSystemConfig
            @ActorUserId = :actor_id, @ConfigKey = :config_key,
            @ConfigValue = :config_value, @Description = :description
    """), {"actor_id": str(actor_id), "config_key": config_key,
           "config_value": config_value, "description": description}).mappings().one()


def delete_config(db: Session, *, actor_id: UUID, config_key: str) -> None:
    db.execute(_procedure_sql("""
        EXEC core.usp_DeleteSystemConfig
            @ActorUserId = :actor_id, @ConfigKey = :config_key
    """), {"actor_id": str(actor_id), "config_key": config_key}).close()


def list_pending_verifications(db: Session, *, reviewer_id: UUID, limit: int,
                               offset: int) -> list[Mapping[str, Any]]:
    return list(db.execute(_procedure_sql("""
        EXEC core.usp_GetPendingVerifications
            @ReviewerUserId = :reviewer_id, @Limit = :limit, @Offset = :offset
    """), {"reviewer_id": str(reviewer_id), "limit": limit, "offset": offset}).mappings().all())


def review_verification(db: Session, *, reviewer_id: UUID, verification_id: UUID,
                        decision: str) -> Mapping[str, Any]:
    return db.execute(_procedure_sql("""
        EXEC core.usp_ReviewMemberVerification
            @VerificationId = :verification_id,
            @ReviewerUserId = :reviewer_id, @Decision = :decision
    """), {"verification_id": str(verification_id), "reviewer_id": str(reviewer_id),
           "decision": decision}).mappings().one()


def get_statistics(db: Session, actor_id: UUID) -> list[Mapping[str, Any]]:
    return list(db.execute(_procedure_sql("""
        EXEC reports.usp_GetDashboardStatistics @ActorUserId = :actor_id
    """), {"actor_id": str(actor_id)}).mappings().all())


def list_reported_contents(db: Session, *, status: str, limit: int, offset: int) -> list[Mapping[str, Any]]:
    return list(db.execute(text("""
        SELECT report.Id AS ReportId, report.TargetId, report.TargetType,
               reporter.FullName AS ReporterName, report.Reason, report.Status, report.CreatedAt,
               family.Name AS FamilyName,
               CASE report.TargetType WHEN N'post' THEN post.Content
                    WHEN N'comment' THEN comment.Content WHEN N'photo' THEN media.MediaUrl END AS TargetContent,
               CAST(CASE WHEN post.Id IS NOT NULL OR comment.Id IS NOT NULL
                         OR (media.Id IS NOT NULL AND (media.MediaType = N'image' OR media.MediaType LIKE N'image/%'))
                         THEN 1 ELSE 0 END AS BIT) AS CanResolve
        FROM community.ReportedContents AS report
        INNER JOIN core.Users AS reporter ON reporter.UserId = report.ReportedBy
        LEFT JOIN community.Posts AS post ON report.TargetType = N'post' AND post.Id = report.TargetId
        LEFT JOIN community.Comments AS comment ON report.TargetType = N'comment' AND comment.Id = report.TargetId
        LEFT JOIN community.PostMedia AS media ON report.TargetType = N'photo' AND media.Id = report.TargetId
        LEFT JOIN community.Posts AS parent ON parent.Id = COALESCE(comment.PostId, media.PostId)
        LEFT JOIN core.Families AS family ON family.Id = COALESCE(post.FamilyId, parent.FamilyId)
        WHERE report.Status = :status
        ORDER BY report.CreatedAt, report.Id
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
    """), {"status": status, "limit": limit, "offset": offset}).mappings().all())


def resolve_report(db: Session, *, report_id: UUID, reviewer_id: UUID, decision: str) -> Mapping[str, Any]:
    return db.execute(_procedure_sql("""
        EXEC community.usp_ResolveReportedContent
            @ReportId = :report_id, @ReviewerUserId = :reviewer_id, @Decision = :decision
    """), {"report_id": str(report_id), "reviewer_id": str(reviewer_id), "decision": decision}).mappings().one()
