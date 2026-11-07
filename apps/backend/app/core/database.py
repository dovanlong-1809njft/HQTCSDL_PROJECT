from collections.abc import Generator

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import (
    MSSQL_DB,
    MSSQL_HOST,
    MSSQL_PORT,
    MSSQL_SA_PASSWORD,
    MSSQL_TRUSTED_CONNECTION,
    MSSQL_USER,
)
from app.shared.base_model import Base

_query: dict[str, str] = {"TrustServerCertificate": "yes"}
if MSSQL_TRUSTED_CONNECTION:
    _query["Trusted_Connection"] = "yes"

database_url = URL.create(
    drivername="mssql+mssqlpython",
    username=None if MSSQL_TRUSTED_CONNECTION else MSSQL_USER,
    password=None if MSSQL_TRUSTED_CONNECTION else MSSQL_SA_PASSWORD,
    host=MSSQL_HOST,
    port=MSSQL_PORT,
    database=MSSQL_DB,
    query=_query,
)

engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["Base", "SessionLocal", "database_url", "engine", "get_db"]
