from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Unicode, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Honor(Base):
    __tablename__ = "Honors"
    __table_args__ = {"schema": "heritage"}

    id: Mapped[UUID] = mapped_column("Id", Uuid(as_uuid=True), primary_key=True, default=uuid4)
    member_id: Mapped[UUID] = mapped_column("MemberId", Uuid(as_uuid=True), ForeignKey("genealogy.Members.Id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column("Title", Unicode(200), nullable=False)
    description: Mapped[str | None] = mapped_column("Description", Unicode(1000))
    date_awarded: Mapped[date | None] = mapped_column("DateAwarded", Date)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, nullable=False, server_default=text("SYSUTCDATETIME()"))
