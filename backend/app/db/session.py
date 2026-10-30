import os
from collections.abc import Generator

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

database_url = URL.create(
    drivername="mssql+mssqlpython",
    username=os.getenv("MSSQL_USER", "sa"),
    password=os.getenv("MSSQL_SA_PASSWORD", ""),
    host=os.getenv("MSSQL_HOST", "localhost"),
    port=int(os.getenv("MSSQL_PORT", "1433")),
    database=os.getenv("MSSQL_DB", "FamilyConnect"),
    query={"TrustServerCertificate": "yes"},
)

engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
