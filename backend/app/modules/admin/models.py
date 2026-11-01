from datetime import datetime

from sqlalchemy import DateTime, Unicode, UnicodeText, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SystemConfig(Base):
    __tablename__ = "SystemConfigs"
    __table_args__ = {"schema": "core"}

    config_key: Mapped[str] = mapped_column("ConfigKey", Unicode(100), primary_key=True)
    config_value: Mapped[str] = mapped_column("ConfigValue", UnicodeText, nullable=False)
    description: Mapped[str | None] = mapped_column("Description", Unicode(500))
    updated_at: Mapped[datetime] = mapped_column("UpdatedAt", DateTime, nullable=False, server_default=text("SYSUTCDATETIME()"))
