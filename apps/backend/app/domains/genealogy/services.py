# Dieu phoi nghiep vu / goi SDK ben ngoai cho domain genealogy
from uuid import UUID

from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.domains.genealogy import repository
from app.domains.genealogy.schemas import (
    DirectoryMemberResponse,
    DirectorySearchResponse,
)


def search_directory_service(
    db: Session,
    *,
    family_id: UUID,
    keyword: str | None,
    occupation: str | None,
    only_current_job: bool,
    education: str | None,
    branch_id: UUID | None,
    generation: int | None,
    root_member_id: UUID | None,
    page: int,
    page_size: int,
) -> DirectorySearchResponse:
    try:
        rows = repository.search_directory(
            db,
            family_id=family_id,
            keyword=keyword,
            occupation=occupation,
            only_current_job=only_current_job,
            education=education,
            branch_id=branch_id,
            generation=generation,
            root_member_id=root_member_id,
            page_number=page,
            page_size=page_size,
        )
    except DBAPIError as exc:
        db.rollback()
        raise RuntimeError("Không thể tìm kiếm danh bạ trong cơ sở dữ liệu.") from exc

    items = [
        DirectoryMemberResponse(
            id=row["Id"],
            full_name=row["FullName"],
            birth_date=row["BirthDate"],
            location=row["Location"],
            family_id=row["FamilyId"],
            branch_id=row["BranchId"],
            generation=row["Generation"],
            latest_position=row["LatestPosition"],
            latest_company=row["LatestCompany"],
            latest_institution=row["LatestInstitution"],
            latest_degree=row["LatestDegree"],
        )
        for row in rows
    ]

    total = int(rows[0]["TotalCount"]) if rows else 0

    return DirectorySearchResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )