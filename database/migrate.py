"""Apply the checked-in SQL objects without running seed or resetting data."""
import re
import sys
import time
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

SQL_ROOT = Path(__file__).resolve().parent


def apply_scripts(connection, database: str, root: Path = SQL_ROOT) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_]+", database) or database.lower() in {"master", "model", "msdb", "tempdb"}:
        raise ValueError("Use a non-system MSSQL_DB containing only letters, numbers and underscores.")
    files = [path for folder in ("schema", "views", "procedures", "triggers")
             for path in sorted((root / folder).glob("*.sql")) if path.name != "00_schemas.sql"]
    for path in files:
        script = path.read_text(encoding="utf-8-sig").replace("$(DB_NAME)", database)
        for batch in re.split(r"(?im)^\s*GO\s*(?:--[^\r\n]*)?\r?$", script):
            if batch.strip():
                connection.exec_driver_sql(batch).close()
        print(f"Applied {path.parent.name}/{path.name}", flush=True)


def main() -> None:
    sys.path.insert(0, str(Path.cwd()))
    sys.path.insert(0, str(SQL_ROOT.parent / "apps" / "backend"))
    from app.core.database import database_url

    database = database_url.database
    if not database or not re.fullmatch(r"[A-Za-z0-9_]+", database) or database.lower() in {"master", "model", "msdb", "tempdb"}:
        raise ValueError("MSSQL_DB must name a non-system database.")
    master = create_engine(database_url.set(database="master"), isolation_level="AUTOCOMMIT")
    for attempt in range(30):
        try:
            with master.connect() as connection:
                if connection.execute(text("SELECT DB_ID(:name)"), {"name": database}).scalar() is None:
                    connection.exec_driver_sql(f"CREATE DATABASE [{database}]").close()
            break
        except OperationalError:
            if attempt == 29:
                raise
            time.sleep(2)
    master.dispose()
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            for schema in ("core", "genealogy", "community", "reports", "heritage"):
                connection.exec_driver_sql(f"IF SCHEMA_ID(N'{schema}') IS NULL EXEC(N'CREATE SCHEMA [{schema}]')").close()
            apply_scripts(connection, database)
    finally:
        engine.dispose()
    print("Migration committed; seed was not run.")


if __name__ == "__main__":
    main()
