from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role
from app.domains.admin import services
from app.domains.admin.schemas import (
    ConfigKey,
    PendingVerificationResponse,
    ReviewVerificationRequest,
    ReviewVerificationResponse,
    SystemConfigCreate,
    SystemConfigResponse,
    SystemConfigUpdate,
)
from app.domains.identity.models import User

router = APIRouter(prefix="/admin", tags=["admin"])

Database = Annotated[Session, Depends(get_db)]
Admin = Annotated[User, Depends(require_role("admin"))]
Reviewer = Annotated[User, Depends(require_role("admin", "family_head"))]
PageLimit = Annotated[int, Query(ge=1, le=200)]
PageOffset = Annotated[int, Query(ge=0, le=2147483647)]


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
