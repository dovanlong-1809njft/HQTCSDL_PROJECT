from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "Users"
    __table_args__ = (
        UniqueConstraint("Email", name="UQ_Users_Email"),
        {"schema": "core"},
    )

    id: Mapped[UUID] = mapped_column("UserId", Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column("Email", String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column("PasswordHash", String(255), nullable=False)
    full_name: Mapped[str] = mapped_column("FullName", String(200), nullable=False)
    role: Mapped[str] = mapped_column("Role", String(20), nullable=False, server_default=text("N'member'"))
    is_active: Mapped[bool] = mapped_column("IsActive", Boolean, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, nullable=False, server_default=text("SYSUTCDATETIME()"))
