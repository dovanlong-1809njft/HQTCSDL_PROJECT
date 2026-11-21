"""Targeted event/profile migration. Dry run unless explicitly passed --apply."""
import argparse
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FILES=("schema/10_event_completion.sql","views/03_community_views.sql","procedures/09_directory_procs.sql","procedures/13_event_completion_procs.sql")


def apply(connection,database):
    for name in FILES:
        script=(ROOT/name).read_text(encoding="utf-8-sig").replace("$(DB_NAME)",database)
        for batch in re.split(r"(?im)^\s*GO\s*$",script):
            if batch.strip():connection.exec_driver_sql(batch).close()


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args()
    if not args.apply:
        print("Dry run: no database connection.\n"+"\n".join(FILES))
    else:
        sys.path.insert(0,str(ROOT.parent/"apps/backend"))
        from app.core.database import database_url
        from sqlalchemy import create_engine
        name=database_url.database
        if not name or not re.fullmatch(r"[A-Za-z0-9_]+",name) or name.lower() in ("master","model","msdb","tempdb"):
            raise ValueError("Use an existing application database")
        engine=create_engine(database_url)
        with engine.begin() as connection:apply(connection,name)
        engine.dispose()
        print("Event/profile migration committed. No seed was run.")
