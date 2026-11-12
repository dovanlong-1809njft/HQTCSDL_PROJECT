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
