from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domains.identity.models import User


def require_family_access(db: Session, actor: User, family_id: UUID, *, manage: bool = False) -> None:
    if actor.role not in ("admin", "family_head", "member") or (manage and actor.role == "member"):
        raise HTTPException(403, "Bạn không có quyền thực hiện thao tác này.")
    row = db.execute(text("""
        SELECT f.Id, CASE WHEN EXISTS (
            SELECT 1 FROM genealogy.Members m
            WHERE m.UserId=:actor_id AND m.FamilyId=f.Id
        ) THEN 1 ELSE 0 END AS IsMember
        FROM core.Families f WHERE f.Id=:family_id
    """), {"actor_id": str(actor.id), "family_id": str(family_id)}).mappings().one_or_none()
    if row is None:
        raise HTTPException(404, "Không tìm thấy gia đình.")
    if actor.role != "admin" and not row["IsMember"]:
        raise HTTPException(403, "Bạn không có quyền truy cập gia đình này.")
