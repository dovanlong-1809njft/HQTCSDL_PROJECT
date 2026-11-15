"""Deploy only comment reactions to an existing database; dry run by default."""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = (ROOT / "schema/09_comment_reactions.sql", ROOT / "procedures/12_comment_reactions_procs.sql")


def apply(connection):
    for path in SCRIPTS:
        for batch in re.split(r"(?im)^\s*GO\s*$", path.read_text(encoding="utf-8-sig")):
            if batch.strip():
                connection.exec_driver_sql(batch).close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply the two reviewed scripts in one transaction")
    args = parser.parse_args()
    if not args.apply:
        print("Dry run; no database connection. Scripts:")
        for script in SCRIPTS:
            print(script.relative_to(ROOT))
    else:
        sys.path.insert(0, str(ROOT.parent / "apps/backend"))
        from sqlalchemy import create_engine, text
        from app.core.database import database_url
        if not database_url.database or database_url.database.lower() in {"master", "model", "msdb", "tempdb"}:
            raise ValueError("An existing application database is required")
        engine = create_engine(database_url)
        with engine.begin() as connection:
            for table in ("community.Comments", "community.Posts", "core.Users"):
                if connection.execute(text("SELECT OBJECT_ID(:name, 'U')"), {"name": table}).scalar() is None:
                    raise RuntimeError("Required application schema is missing")
            apply(connection)
        engine.dispose()
        print("Comment reactions migration committed. No seed was run.")
