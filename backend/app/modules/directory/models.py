from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Unicode, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Member(Base):
    __tablename__ = "Members"
    __table_args__ = {"schema": "genealogy"}

    id: Mapped[UUID] = mapped_column("Id", Uuid(as_uuid=True), primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column("FamilyId", Uuid(as_uuid=True), ForeignKey("core.Families.Id"), nullable=False)
    branch_id: Mapped[UUID | None] = mapped_column("BranchId", Uuid(as_uuid=True), ForeignKey("core.Branches.Id"))
    user_id: Mapped[UUID | None] = mapped_column("UserId", Uuid(as_uuid=True), ForeignKey("core.Users.UserId"))
    full_name: Mapped[str] = mapped_column("FullName", Unicode(200), nullable=False)
    birth_date: Mapped[date | None] = mapped_column("BirthDate", Date)
    location: Mapped[str | None] = mapped_column("Location", Unicode(300))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, nullable=False, server_default=text("SYSUTCDATETIME()"))


class Education(Base):
    __tablename__ = "Educations"
    __table_args__ = {"schema": "genealogy"}

    id: Mapped[UUID] = mapped_column("Id", Uuid(as_uuid=True), primary_key=True, default=uuid4)
    member_id: Mapped[UUID] = mapped_column("MemberId", Uuid(as_uuid=True), ForeignKey("genealogy.Members.Id", ondelete="CASCADE"), nullable=False)
    institution: Mapped[str] = mapped_column("Institution", Unicode(200), nullable=False)
    degree: Mapped[str | None] = mapped_column("Degree", Unicode(200))
    start_date: Mapped[date | None] = mapped_column("StartDate", Date)
    end_date: Mapped[date | None] = mapped_column("EndDate", Date)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, nullable=False, server_default=text("SYSUTCDATETIME()"))


class WorkHistory(Base):
    __tablename__ = "WorkHistories"
    __table_args__ = {"schema": "genealogy"}

    id: Mapped[UUID] = mapped_column("Id", Uuid(as_uuid=True), primary_key=True, default=uuid4)
    member_id: Mapped[UUID] = mapped_column("MemberId", Uuid(as_uuid=True), ForeignKey("genealogy.Members.Id", ondelete="CASCADE"), nullable=False)
    company: Mapped[str] = mapped_column("Company", Unicode(200), nullable=False)
    position: Mapped[str] = mapped_column("Position", Unicode(200), nullable=False)
    start_date: Mapped[date | None] = mapped_column("StartDate", Date)
    end_date: Mapped[date | None] = mapped_column("EndDate", Date)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, nullable=False, server_default=text("SYSUTCDATETIME()"))
