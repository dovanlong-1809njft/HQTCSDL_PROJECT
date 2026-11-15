"""Actual application + JWT + SQL for upload E2E; refuses the primary database."""
import sys
import os
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"apps/backend"))
from sqlalchemy import text
from app.core.database import database_url,engine
from app.core.security import hash_password

if not database_url.database or not database_url.database.endswith("_Reactions_Test"):
    raise RuntimeError("Upload QA server requires the isolated _Reactions_Test database")

if os.environ.get("UPLOAD_QA_INIT_SCHEMA")=="1":
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"database"))
    from migrate import apply_scripts
    with engine.begin() as c:
        for schema in ("core","genealogy","community","heritage","reports"):
            c.exec_driver_sql(f"IF SCHEMA_ID(N'{schema}') IS NULL EXEC(N'CREATE SCHEMA [{schema}]')").close()
        apply_scripts(c,database_url.database)

FAMILY="e0100000-0000-0000-0000-000000000001"
USERS=[("e0200000-0000-0000-0000-000000000001","upload-one@example.com"),
       ("e0200000-0000-0000-0000-000000000002","upload-two@example.com"),
       ("e0200000-0000-0000-0000-000000000003","upload-outsider@example.com")]
with engine.begin() as c:
    c.execute(text("IF NOT EXISTS(SELECT 1 FROM core.Families WHERE Id=:id) INSERT core.Families(Id,Name) VALUES(:id,N'Upload QA family')"),{"id":FAMILY})
    for index,(identifier,email) in enumerate(USERS):
        c.execute(text("""IF NOT EXISTS(SELECT 1 FROM core.Users WHERE UserId=:id)
            INSERT core.Users(UserId,Email,PasswordHash,FullName,Role)
            VALUES(:id,:email,:password,N'Upload QA member','member')"""),{"id":identifier,"email":email,"password":hash_password("UploadTestOnly!2026")})
        if index<2:
            c.execute(text("""IF NOT EXISTS(SELECT 1 FROM genealogy.Members WHERE UserId=:id)
                INSERT genealogy.Members(UserId,FamilyId,FullName) VALUES(:id,:family,N'Upload QA member')"""),{"id":identifier,"family":FAMILY})

if __name__=="__main__":
    import uvicorn
    uvicorn.run("app.main:app",host="0.0.0.0",port=8000)
