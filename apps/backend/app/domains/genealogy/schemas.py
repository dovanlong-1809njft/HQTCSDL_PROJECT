# Pydantic request/response DTO cho domain genealogy
from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.shared.pagination import PaginatedResponse


class DirectoryMemberResponse(BaseModel):
    id: UUID
    full_name: str
    birth_date: date | None = None
    location: str | None = None
    family_id: UUID
    branch_id: UUID | None = None
    generation: int
    latest_position: str | None = None
    latest_company: str | None = None
    latest_institution: str | None = None
    latest_degree: str | None = None


DirectorySearchResponse = PaginatedResponse[DirectoryMemberResponse]