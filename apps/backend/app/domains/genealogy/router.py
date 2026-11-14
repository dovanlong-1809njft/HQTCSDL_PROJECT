from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.domains.genealogy.schemas import (
    AddChildNodeRequest,
    AddMarriageRequest,
    DirectorySearchResponse,
    MemberCreateRequest,
    MemberResponse,
    MemberUpdateRequest,
)
from app.domains.genealogy.services import (
    add_child_service,
    add_marriage_service,
    create_member_service,
    delete_member_service,
    get_member_service,
    list_members_service,
    search_directory_service,
    update_member_service,
)
from app.domains.identity.models import User

router = APIRouter(prefix="/genealogy", tags=["genealogy"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


# ---------- Directory (đã có) ----------
@router.get("/directory", response_model=DirectorySearchResponse)
def search_directory(
    family_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    keyword: Annotated[str | None, Query(max_length=200)] = None,
    occupation: Annotated[str | None, Query(max_length=200)] = None,
    only_current_job: bool = False,
    education: Annotated[str | None, Query(max_length=200)] = None,
    branch_id: UUID | None = None,
    generation: Annotated[int | None, Query(ge=1)] = None,
    root_member_id: UUID | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> DirectorySearchResponse:
    return search_directory_service(
        db,
        family_id=family_id,
        keyword=keyword,
        occupation=occupation,
        only_current_job=only_current_job,
        education=education,
        branch_id=branch_id,
        generation=generation,
        root_member_id=root_member_id,
        page=page,
        page_size=page_size,
    )


# ---------- Member ----------
@router.post(
    "/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_member(
    payload: MemberCreateRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> MemberResponse:
    return create_member_service(db, payload)


@router.get("/members", response_model=list[MemberResponse])
def list_members(
    family_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    branch_id: UUID | None = None,
) -> list[MemberResponse]:
    return list_members_service(db, family_id, branch_id)


@router.get("/members/{member_id}", response_model=MemberResponse)
def get_member(
    member_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> MemberResponse:
    return get_member_service(db, member_id)


@router.put("/members/{member_id}", response_model=MemberResponse)
def update_member(
    member_id: UUID,
    payload: MemberUpdateRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> MemberResponse:
    return update_member_service(db, member_id, payload)


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(
    member_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    delete_member_service(db, member_id)


# ---------- Quan hệ gia phả ----------
@router.post(
    "/relationships/child",
    response_model=dict[str, str],
    status_code=status.HTTP_201_CREATED,
)
def add_child_relationship(
    payload: AddChildNodeRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    return add_child_service(db, payload)


@router.post(
    "/relationships/marriage",
    response_model=dict[str, str],
    status_code=status.HTTP_201_CREATED,
)
def add_marriage_relationship(
    payload: AddMarriageRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    return add_marriage_service(db, payload)