from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.domains.genealogy.schemas import DirectorySearchResponse
from app.domains.genealogy.services import search_directory_service
from app.domains.identity.models import User

router = APIRouter(prefix="/genealogy", tags=["genealogy"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


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