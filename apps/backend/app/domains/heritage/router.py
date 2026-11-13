from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role
from app.domains.identity.models import User
from app.domains.heritage import services
from app.domains.heritage.schemas import (
    FamilyResponse, FamilyTree, HonorCreate, HonorPatch, HonorResponse, ItemCreate,
    ItemPatch, ItemResponse, ItemType, MemberResponse, RankingResponse, Version,
)
from app.shared.pagination import PaginatedResponse

router = APIRouter(prefix="/heritage", tags=["heritage"])

Database = Annotated[Session, Depends(get_db)]
Reader = Annotated[User, Depends(require_role("admin", "family_head", "member"))]
Manager = Annotated[User, Depends(require_role("admin", "family_head"))]
Page = Annotated[int, Query(ge=1, le=1000000)]
Size = Annotated[int, Query(ge=1, le=100)]
Search = Annotated[str, Query(max_length=200)]


@router.get("/families", response_model=list[FamilyResponse])
def families(db: Database, actor: Reader):
    return services.families(db, actor)


@router.get("/items", response_model=PaginatedResponse[ItemResponse])
def items(family_id: UUID, db: Database, actor: Reader, page: Page = 1, page_size: Size = 12,
          q: Search = "", item_type: ItemType | None = None):
    return services.list_resource(db, actor, family_id, "items", page=page, page_size=page_size, q=q, item_type=item_type)


@router.get("/items/{identifier}", response_model=ItemResponse)
def item(identifier: UUID, family_id: UUID, db: Database, actor: Reader):
    return services.read(db, actor, family_id, "items", identifier)


@router.post("/items", response_model=ItemResponse, status_code=201)
def create_item(family_id: UUID, payload: ItemCreate, db: Database, actor: Reader):
    return services.mutate(db, actor, family_id, "items", "create", payload)


@router.patch("/items/{identifier}", response_model=ItemResponse)
def patch_item(identifier: UUID, family_id: UUID, payload: ItemPatch, db: Database, actor: Reader):
    return services.mutate(db, actor, family_id, "items", "update", payload, identifier)


@router.delete("/items/{identifier}", status_code=204)
def delete_item(identifier: UUID, family_id: UUID, expected_version: Version, db: Database, actor: Reader):
    services.mutate(db, actor, family_id, "items", "delete", identifier=identifier, expected_version=expected_version)
    return Response(status_code=204)


@router.get("/honors", response_model=PaginatedResponse[HonorResponse])
def honors(family_id: UUID, db: Database, actor: Reader, page: Page = 1, page_size: Size = 12, q: Search = ""):
    return services.list_resource(db, actor, family_id, "honors", page=page, page_size=page_size, q=q)


@router.get("/honors/{identifier}", response_model=HonorResponse)
def honor(identifier: UUID, family_id: UUID, db: Database, actor: Reader):
    return services.read(db, actor, family_id, "honors", identifier)


@router.post("/honors", response_model=HonorResponse, status_code=201)
def create_honor(family_id: UUID, payload: HonorCreate, db: Database, actor: Manager):
    return services.mutate(db, actor, family_id, "honors", "create", payload)


@router.patch("/honors/{identifier}", response_model=HonorResponse)
def patch_honor(identifier: UUID, family_id: UUID, payload: HonorPatch, db: Database, actor: Manager):
    return services.mutate(db, actor, family_id, "honors", "update", payload, identifier)


@router.delete("/honors/{identifier}", status_code=204)
def delete_honor(identifier: UUID, family_id: UUID, expected_version: Version, db: Database, actor: Manager):
    services.mutate(db, actor, family_id, "honors", "delete", identifier=identifier, expected_version=expected_version)
    return Response(status_code=204)


@router.get("/ranking", response_model=PaginatedResponse[RankingResponse])
def ranking(family_id: UUID, db: Database, actor: Reader, page: Page = 1, page_size: Size = 20, q: Search = ""):
    return services.list_resource(db, actor, family_id, "ranking", page=page, page_size=page_size, q=q)


@router.get("/members", response_model=PaginatedResponse[MemberResponse])
def members(family_id: UUID, db: Database, actor: Reader, page: Page = 1, page_size: Size = 50, q: Search = ""):
    # Read-only selector for honors; TV2 retains member CRUD ownership.
    return services.list_resource(db, actor, family_id, "members", page=page, page_size=page_size, q=q)


@router.get("/family-tree", response_model=FamilyTree)
def family_tree(family_id: UUID, db: Database, actor: Reader):
    return services.tree(db, actor, family_id)
