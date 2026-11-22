from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role
from app.core.security import verify_password
from app.domains.admin import services
from app.domains.admin.backups import DatabaseBackups, get_database_backups
from app.domains.admin.schemas import (
    BackupResponse,
    BackupsResponse,
    RestoreRequest,
    RestoreResponse,
    ConfigKey,
    FamilyActivityResponse,
    PendingVerificationResponse,
    ReportedContentResponse,
    ReportStatus,
    ResolveReportRequest,
    ResolveReportResponse,
    ReviewVerificationRequest,
    ReviewVerificationResponse,
    SystemConfigCreate,
    SystemConfigResponse,
    SystemConfigUpdate,
    SiteSettings,
)
from app.domains.identity.models import User

router = APIRouter(prefix="/admin", tags=["admin"])
public_router = APIRouter(prefix="/settings", tags=["settings"])

Database = Annotated[Session, Depends(get_db)]
Admin = Annotated[User, Depends(require_role("admin"))]
Reviewer = Annotated[User, Depends(require_role("admin", "family_head"))]
PageLimit = Annotated[int, Query(ge=1, le=200)]
PageOffset = Annotated[int, Query(ge=0, le=2147483647)]
Backups = Annotated[DatabaseBackups, Depends(get_database_backups)]


@router.get("/backups", response_model=BackupsResponse)
def list_backups(current_user: Admin, backups: Backups, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return backups.list()


@router.post("/backups", response_model=BackupResponse, status_code=201)
def create_backup(current_user: Admin, backups: Backups):
    return backups.create(current_user.id)


@router.delete("/backups/{backup_id}", status_code=204)
def delete_backup(backup_id: UUID, current_user: Admin, backups: Backups):
    backups.delete(backup_id, current_user.id)
    return Response(status_code=204)


@router.post("/backups/{backup_id}/restore", response_model=RestoreResponse)
def restore_backup(backup_id: UUID, payload: RestoreRequest, db: Database,
                   current_user: Admin, backups: Backups):
    if payload.database != backups.database:
        raise HTTPException(422, "Nhập chính xác tên database để xác nhận khôi phục.")
    if not verify_password(payload.password.get_secret_value(), current_user.password_hash):
        raise HTTPException(403, "Mật khẩu quản trị không đúng.")
    actor_id = current_user.id
    # Release our own read connection before taking the exclusive maintenance lock.
    db.close()
    release = db.info.pop("release_database_access", None)
    if release:
        release()
    return backups.restore(backup_id, actor_id)


@public_router.get("", response_model=SiteSettings)
def public_site_settings(db: Database, response: Response) -> SiteSettings:
    response.headers["Cache-Control"] = "no-store"
    return services.get_site_settings(db)


@router.put("/site-settings", response_model=SiteSettings)
def save_site_settings(payload: SiteSettings, db: Database, current_user: Admin) -> SiteSettings:
    return services.save_site_settings(db, payload, current_user.id)


@router.get("/configs", response_model=list[SystemConfigResponse])
def list_configs(db: Database, current_user: Admin, limit: PageLimit = 50,
                 offset: PageOffset = 0) -> list[SystemConfigResponse]:
    return services.list_configs(db, limit=limit, offset=offset)


@router.get("/configs/{config_key}", response_model=SystemConfigResponse)
def get_config(config_key: ConfigKey, db: Database, current_user: Admin) -> SystemConfigResponse:
    return services.get_config(db, config_key)


@router.post("/configs", response_model=SystemConfigResponse, status_code=status.HTTP_201_CREATED)
def create_config(payload: SystemConfigCreate, db: Database, current_user: Admin) -> SystemConfigResponse:
    return services.create_config(db, payload, current_user.id)


@router.put("/configs/{config_key}", response_model=SystemConfigResponse)
def update_config(config_key: ConfigKey, payload: SystemConfigUpdate, db: Database,
                  current_user: Admin) -> SystemConfigResponse:
    return services.update_config(db, config_key, payload, current_user.id)


@router.delete("/configs/{config_key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_config(config_key: ConfigKey, db: Database, current_user: Admin) -> Response:
    services.delete_config(db, config_key, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/verifications/pending", response_model=list[PendingVerificationResponse])
def list_pending_verifications(db: Database, current_user: Reviewer, limit: PageLimit = 50,
                               offset: PageOffset = 0) -> list[PendingVerificationResponse]:
    return services.list_pending_verifications(db, current_user.id, limit=limit, offset=offset)


@router.patch("/verifications/{verification_id}/review", response_model=ReviewVerificationResponse)
def review_verification(verification_id: UUID, payload: ReviewVerificationRequest, db: Database,
                        current_user: Reviewer) -> ReviewVerificationResponse:
    return services.review_verification(db, verification_id, payload, current_user.id)


@router.get("/statistics", response_model=list[FamilyActivityResponse])
def get_statistics(db: Database, current_user: Reviewer) -> list[FamilyActivityResponse]:
    """Admin xem tất cả; family_head chỉ xem gia đình có hồ sơ đã liên kết."""
    return services.get_statistics(db, current_user.id)


@router.get("/reports", response_model=list[ReportedContentResponse])
def list_reported_contents(db: Database, current_user: Admin, status: ReportStatus = "pending",
                           limit: PageLimit = 50, offset: PageOffset = 0) -> list[ReportedContentResponse]:
    return services.list_reported_contents(db, status=status, limit=limit, offset=offset)


@router.patch("/reports/{report_id}/resolve", response_model=ResolveReportResponse)
def resolve_report(report_id: UUID, payload: ResolveReportRequest, db: Database,
                   current_user: Admin) -> ResolveReportResponse:
    """resolved xóa nội dung và đóng báo cáo liên quan; dismissed giữ nguyên nội dung."""
    return services.resolve_report(db, report_id, payload, current_user.id)
