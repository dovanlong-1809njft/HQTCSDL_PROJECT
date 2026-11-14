# Goi truc tiep Stored Procedure / View / Function duoi SQL Server cho domain genealogy
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def search_directory(
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
    page_number: int,
    page_size: int,
) -> list[Mapping[str, Any]]:
    statement = text(
        """
        EXEC genealogy.usp_SearchDirectory
            @FamilyId = :family_id,
            @Keyword = :keyword,
            @Occupation = :occupation,
            @OnlyCurrentJob = :only_current_job,
            @Education = :education,
            @BranchId = :branch_id,
            @Generation = :generation,
            @RootMemberId = :root_member_id,
            @PageNumber = :page_number,
            @PageSize = :page_size
        """
    )

    result = db.execute(
        statement,
        {
            "family_id": str(family_id),
            "keyword": keyword,
            "occupation": occupation,
            "only_current_job": only_current_job,
            "education": education,
            "branch_id": str(branch_id) if branch_id else None,
            "generation": generation,
            "root_member_id": str(root_member_id) if root_member_id else None,
            "page_number": page_number,
            "page_size": page_size,
        },
    )

    return result.mappings().all()