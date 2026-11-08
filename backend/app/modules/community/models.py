from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Unicode, UnicodeText, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Event(Base):
    __tablename__ = "Events"
    __table_args__ = {"schema": "community"}

    id: Mapped[UUID] = mapped_column("Id", Uuid(as_uuid=True), primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column("FamilyId", Uuid(as_uuid=True), ForeignKey("core.Families.Id"), nullable=False)
    title: Mapped[str] = mapped_column("Title", Unicode(200), nullable=False)
    event_date: Mapped[datetime] = mapped_column("EventDate", DateTime, nullable=False)
    location: Mapped[str | None] = mapped_column("Location", Unicode(500))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, nullable=False, server_default=text("SYSUTCDATETIME()"))


class EventReminder(Base):
    __tablename__ = "EventReminders"
    __table_args__ = {"schema": "community"}

    id: Mapped[UUID] = mapped_column("Id", Uuid(as_uuid=True), primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column("EventId", Uuid(as_uuid=True), ForeignKey("community.Events.Id", ondelete="CASCADE"), nullable=False)
    reminder_time: Mapped[datetime] = mapped_column("ReminderTime", DateTime, nullable=False)
    status: Mapped[str] = mapped_column("Status", Unicode(20), nullable=False, server_default=text("N'pending'"))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, nullable=False, server_default=text("SYSUTCDATETIME()"))


class EventGallery(Base):
    __tablename__ = "EventGalleries"
    __table_args__ = {"schema": "community"}

    id: Mapped[UUID] = mapped_column("Id", Uuid(as_uuid=True), primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column("EventId", Uuid(as_uuid=True), ForeignKey("community.Events.Id", ondelete="CASCADE"), nullable=False)
    media_url: Mapped[str] = mapped_column("MediaUrl", Unicode(2048), nullable=False)
    uploaded_by: Mapped[UUID] = mapped_column("UploadedBy", Uuid(as_uuid=True), ForeignKey("core.Users.UserId"), nullable=False)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, nullable=False, server_default=text("SYSUTCDATETIME()"))


class Post(Base):
    __tablename__ = "Posts"
    __table_args__ = {"schema": "community"}

    id: Mapped[UUID] = mapped_column("Id", Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column("UserId", Uuid(as_uuid=True), ForeignKey("core.Users.UserId"), nullable=False)
    family_id: Mapped[UUID] = mapped_column("FamilyId", Uuid(as_uuid=True), ForeignKey("core.Families.Id"), nullable=False)
    content: Mapped[str] = mapped_column("Content", UnicodeText, nullable=False)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, nullable=False, server_default=text("SYSUTCDATETIME()"))


class PostMedia(Base):
    __tablename__ = "PostMedia"
    __table_args__ = {"schema": "community"}

    id: Mapped[UUID] = mapped_column("Id", Uuid(as_uuid=True), primary_key=True, default=uuid4)
    post_id: Mapped[UUID] = mapped_column("PostId", Uuid(as_uuid=True), ForeignKey("community.Posts.Id", ondelete="CASCADE"), nullable=False)
    media_url: Mapped[str] = mapped_column("MediaUrl", Unicode(2048), nullable=False)
    media_type: Mapped[str] = mapped_column("MediaType", Unicode(50), nullable=False, server_default=text("N'image'"))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, nullable=False, server_default=text("SYSUTCDATETIME()"))


class ReportedContent(Base):
    __tablename__ = "ReportedContents"
    __table_args__ = {"schema": "community"}

    id: Mapped[UUID] = mapped_column("Id", Uuid(as_uuid=True), primary_key=True, default=uuid4)
    target_id: Mapped[UUID] = mapped_column("TargetId", Uuid(as_uuid=True), nullable=False)
    target_type: Mapped[str] = mapped_column("TargetType", Unicode(50), nullable=False)
    reported_by: Mapped[UUID] = mapped_column("ReportedBy", Uuid(as_uuid=True), ForeignKey("core.Users.UserId"), nullable=False)
    reason: Mapped[str] = mapped_column("Reason", Unicode(500), nullable=False)
    status: Mapped[str] = mapped_column("Status", Unicode(20), nullable=False, server_default=text("N'pending'"))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, nullable=False, server_default=text("SYSUTCDATETIME()"))
