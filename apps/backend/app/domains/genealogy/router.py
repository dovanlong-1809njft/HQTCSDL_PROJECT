from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_role
from app.domains.genealogy import repository as repo
from app.domains.genealogy.schemas import (
    DirectorySearchResponse,
    MemberFields,
    NameFields,
    ProfileFields,
    RelationshipFields,
    VerificationRequest,
)
from app.domains.genealogy.services import run, search_directory_service
from app.domains.identity.models import User

router = APIRouter(prefix="/genealogy", tags=["genealogy"])
DB = Annotated[Session, Depends(get_db)]
Actor = Annotated[User, Depends(get_current_user)]
Manager = Annotated[User, Depends(require_role("admin", "family_head"))]
Member = Annotated[User, Depends(require_role("admin", "family_head", "member"))]
Resource = Literal["branches", "members"]
Kind = Literal["parent-child", "marriages"]


@router.get("/directory", response_model=DirectorySearchResponse)
def search_directory(
    family_id: UUID,
    current_user: Actor,
    db: DB,
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


@router.get("/me")
def profile(db: DB, actor: Actor):
    return run(db, lambda: repo.profile(db, actor.id))


@router.put("/me")
def update_profile(payload: ProfileFields, db: DB, actor: Actor):
    def operation():
        if repo.profile(db, actor.id)["member"] and (payload.birth_date is None or not payload.location):
            raise HTTPException(422, "Cần nhập đầy đủ ngày sinh và nơi ở của hồ sơ đã liên kết.")
        repo.execute(
            db,
            "EXEC genealogy.usp_UpdateOwnProfile @ActorUserId=:actor,@Name=:name,@BirthDate=:birth_date,@Location=:location",
            dict(actor=actor.id, **payload.model_dump(exclude={"branch_id"})),
        ).close()
        return repo.profile(db, actor.id)

    return run(db, operation, write=True)


@router.get("/verification-candidates")
def candidates(
    db: DB,
    actor: Member,
    family_name: str = Query(min_length=2, max_length=200),
    full_name: str = Query(min_length=2, max_length=200),
    birth_date: date | None = None,
):
    return run(db, lambda: repo.candidates(db, family_name.strip(), full_name.strip(), birth_date))


@router.post("/verifications", status_code=201)
def request_verification(payload: VerificationRequest, db: DB, actor: Member):
    def operation():
        repo.execute(
            db,
            "EXEC core.usp_RequestMemberVerification @ActorUserId=:actor,@MemberId=:member",
            dict(actor=actor.id, member=payload.member_id),
        ).close()
        return repo.profile(db, actor.id)

    return run(db, operation, write=True)


@router.post("/families", status_code=201)
def create_family(payload: NameFields, db: DB, actor: Annotated[User, Depends(require_role("admin"))]):
    return run(db, lambda: repo.mutate(db, actor.id, None, "families", "create", None, payload.model_dump()), write=True)


@router.put("/families/{family_id}")
def update_family(family_id: UUID, payload: NameFields, db: DB, actor: Manager):
    return run(db, lambda: repo.mutate(db, actor.id, family_id, "families", "update", None, payload.model_dump()), write=True)


@router.delete("/families/{family_id}", status_code=204)
def delete_family(family_id: UUID, db: DB, actor: Annotated[User, Depends(require_role("admin"))]):
    run(db, lambda: repo.mutate(db, actor.id, family_id, "families", "delete", None, {}), write=True)


@router.get("/relationships")
def relationships(family_id: UUID, db: DB, actor: Member, member_id: UUID | None = None):
    return run(db, lambda: repo.relations(db, actor.id, family_id, member_id))


@router.post("/relationships/{kind}", status_code=201)
def add_relationship(kind: Kind, family_id: UUID, payload: RelationshipFields, db: DB, actor: Manager):
    if kind == "marriages" and payload.married_date is None:
        raise HTTPException(422, "Cần nhập ngày kết hôn.")
    params = dict(actor=actor.id, family=family_id, kind=kind, **payload.model_dump())
    return run(
        db,
        lambda: dict(
            repo.execute(
                db,
                "EXEC genealogy.usp_ManageRelationship @ActorUserId=:actor,@FamilyId=:family,@Kind=:kind,@Action='create',@FirstId=:first_id,@SecondId=:second_id,@MarriedDate=:married_date",
                params,
            )
            .mappings()
            .one()
        ),
        write=True,
    )


@router.delete("/relationships/{kind}/{identifier}", status_code=204)
def delete_relationship(kind: Kind, identifier: UUID, family_id: UUID, db: DB, actor: Manager):
    run(
        db,
        lambda: repo.execute(
            db,
            "EXEC genealogy.usp_ManageRelationship @ActorUserId=:actor,@FamilyId=:family,@Kind=:kind,@Action='delete',@Id=:id",
            dict(actor=actor.id, family=family_id, kind=kind, id=identifier),
        ).close(),
        write=True,
    )


@router.get("/{resource}")
def records(
    resource: Resource,
    family_id: UUID,
    db: DB,
    actor: Member,
    q: str = Query(default="", max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    return run(db, lambda: repo.records(db, actor.id, family_id, resource, q, (page - 1) * page_size, page_size))


@router.post("/{resource}", status_code=201)
def create_record(resource: Resource, family_id: UUID, payload: MemberFields, db: DB, actor: Manager):
    values = payload.model_dump() if resource == "members" else {"name": payload.name}
    return run(db, lambda: repo.mutate(db, actor.id, family_id, resource, "create", None, values), write=True)


@router.put("/{resource}/{identifier}")
def update_record(resource: Resource, identifier: UUID, family_id: UUID, payload: MemberFields, db: DB, actor: Manager):
    values = payload.model_dump() if resource == "members" else {"name": payload.name}
    return run(db, lambda: repo.mutate(db, actor.id, family_id, resource, "update", identifier, values), write=True)


@router.delete("/{resource}/{identifier}", status_code=204)
def delete_record(resource: Resource, identifier: UUID, family_id: UUID, db: DB, actor: Manager):
    run(db, lambda: repo.mutate(db, actor.id, family_id, resource, "delete", identifier, {}), write=True)
