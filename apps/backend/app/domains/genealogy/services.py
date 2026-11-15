import re
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.domains.genealogy import repository
from app.domains.genealogy.schemas import (
    DirectoryMemberResponse,
    DirectorySearchResponse,
)


def run(db, operation, write=False):
    try:
        result = operation()
        if write:
            db.commit()
        return result
    except DBAPIError as exc:
        db.rollback()
        marker = re.search(r"\[TV4_SQL:(\d+)\]", str(exc.orig))
        code = int(marker[1]) if marker else 0
        if code == 51403:
            status, message = 403, "Bạn không có quyền thao tác trong gia đình này."
        elif code in (51404, 50102, 50202):
            status, message = 404, "Không tìm thấy dữ liệu."
        elif code in (51509, 2601, 2627, 547, 50103, 50203):
            status, message = 409, "Dữ liệu bị trùng hoặc còn liên kết. Hãy kiểm tra trước khi thay đổi."
        elif code in (50100, 50200, 1205, 1222):
            status, message = 503, "Gia phả đang được xử lý. Vui lòng thử lại."
        elif code in (51522, 50101, 50104, 50105, 50201, 50204, 50205, 50001, 50002):
            status, message = (
                422,
                "Dữ liệu không hợp lệ: kiểm tra chi nhánh, ngày sinh, chu trình, tối đa hai cha/mẹ và quy tắc huyết thống ba đời.",
            )
        else:
            status, message = 500, "Không thể xử lý dữ liệu gia phả."
        raise HTTPException(status, message) from None
    except Exception:
        if write:
            db.rollback()
        raise


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
