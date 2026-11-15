# Goi truc tiep Stored Procedure / View / Function duoi SQL Server cho domain genealogy
from collections.abc import Mapping
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from .schemas import (
    AddChildNodeRequest,
    AddMarriageRequest,
    MemberCreateRequest,
    MemberUpdateRequest,
)

# ... search_directory giữ nguyên ...


# ---------- Member CRUD ----------
# Alias về snake_case để khớp trực tiếp với MemberResponse
_MEMBER_SELECT = """
    Id          AS id,
    FamilyId    AS family_id,
    BranchId    AS branch_id,
    FullName    AS full_name,
    Gender      AS gender,
    BirthDate   AS birth_date,
    DeathDate   AS death_date,
    Location    AS location,
    Bio         AS bio,
    CreatedAt   AS created_at
"""

_MEMBER_OUTPUT = _MEMBER_SELECT.replace("Id ", "INSERTED.Id ", 1)
for _col in (
    "FamilyId", "BranchId", "FullName", "Gender",
    "BirthDate", "DeathDate", "Location", "Bio", "CreatedAt",
):
    _MEMBER_OUTPUT = _MEMBER_OUTPUT.replace(f"{_col} ", f"INSERTED.{_col} ", 1)

# Whitelist: tên field Pydantic -> tên cột SQL (chống SQL injection khi build SET động)
_UPDATABLE_COLUMNS: dict[str, str] = {
    "branch_id": "BranchId",
    "full_name": "FullName",
    "gender": "Gender",
    "birth_date": "BirthDate",
    "death_date": "DeathDate",
    "location": "Location",
    "bio": "Bio",
}


def create_member(db: Session, payload: MemberCreateRequest) -> Mapping[str, Any]:
    member_id = uuid4()
    statement = text(
        f"""
        INSERT INTO genealogy.Members
            (Id, FamilyId, BranchId, FullName, Gender,
             BirthDate, DeathDate, Location, Bio)
        OUTPUT {_MEMBER_OUTPUT}
        VALUES
            (:id, :family_id, :branch_id, :full_name, :gender,
             :birth_date, :death_date, :location, :bio)
        """
    )
    try:
        row = db.execute(
            statement,
            {
                "id": str(member_id),
                "family_id": str(payload.family_id),
                "branch_id": str(payload.branch_id) if payload.branch_id else None,
                "full_name": payload.full_name,
                "gender": payload.gender,
                "birth_date": payload.birth_date,
                "death_date": payload.death_date,
                "location": payload.location,
                "bio": payload.bio,
            },
        ).mappings().one()
        db.commit()
        return row
    except Exception:
        db.rollback()
        raise


def get_member_by_id(db: Session, member_id: UUID) -> Mapping[str, Any] | None:
    statement = text(
        f"SELECT {_MEMBER_SELECT} FROM genealogy.Members WHERE Id = :id"
    )
    return db.execute(statement, {"id": str(member_id)}).mappings().first()


def list_members_by_family(
    db: Session, family_id: UUID
) -> list[Mapping[str, Any]]:
    statement = text(
        f"""
        SELECT {_MEMBER_SELECT}
        FROM genealogy.Members
        WHERE FamilyId = :family_id
        ORDER BY FullName
        """
    )
    return db.execute(statement, {"family_id": str(family_id)}).mappings().all()


def update_member(
    db: Session, member_id: UUID, payload: MemberUpdateRequest
) -> Mapping[str, Any] | None:
    changes = payload.model_dump(exclude_unset=True)

    set_parts: list[str] = []
    params: dict[str, Any] = {"id": str(member_id)}
    for field, value in changes.items():
        column = _UPDATABLE_COLUMNS.get(field)
        if column is None:
            continue
        set_parts.append(f"{column} = :{field}")
        params[field] = str(value) if field == "branch_id" and value else value

    # Không có gì để sửa -> trả lại bản ghi hiện tại
    if not set_parts:
        return get_member_by_id(db, member_id)

    statement = text(
        f"""
        UPDATE genealogy.Members
        SET {", ".join(set_parts)}
        OUTPUT {_MEMBER_OUTPUT}
        WHERE Id = :id
        """
    )
    try:
        row = db.execute(statement, params).mappings().first()
        db.commit()
        return row  # None nếu không tìm thấy member
    except Exception:
        db.rollback()
        raise


def delete_member(db: Session, member_id: UUID) -> bool:
    statement = text("DELETE FROM genealogy.Members WHERE Id = :id")
    try:
        result = db.execute(statement, {"id": str(member_id)})
        db.commit()
        return result.rowcount > 0
    except Exception:
        db.rollback()
        raise


# ---------- Stored Procedure quan hệ ----------
def exec_add_child_node(db: Session, payload: AddChildNodeRequest) -> None:
    statement = text(
        """
        DECLARE @NewId UNIQUEIDENTIFIER;
        EXEC genealogy.usp_AddChildNode
            @ParentId = :p_id,
            @ChildId = :c_id,
             @ParentChildId = @NewId OUTPUT;
        SELECT @NewId AS id;
        """
    )
    try:
        new_id = db.execute(
            statement,
            {"p_id": str(payload.parent_id), "c_id": str(payload.child_id)},
        ).scalar()
        db.commit()
        return UUID(str(new_id)) if new_id else None
    except Exception:
        db.rollback()
        raise


def exec_add_marriage(db: Session, payload: AddMarriageRequest) -> UUID | None:
    statement = text(
        """
        DECLARE @NewId UNIQUEIDENTIFIER;
        EXEC genealogy.usp_AddMarriage
            @MemberAId = :a_id,
            @MemberBId = :b_id,
            @MarriedDate = :married_date,
            @MarriageId = @NewId OUTPUT;
        SELECT @NewId AS id;
        """
    )
    try:
        new_id = db.execute(
            statement,
            {
                "a_id": str(payload.spouse_a_id),
                "b_id": str(payload.spouse_b_id),
                "married_date": payload.marriage_date,
            },
        ).scalar()
        db.commit()
        return UUID(str(new_id)) if new_id else None
    except Exception:
        db.rollback()
        raise
