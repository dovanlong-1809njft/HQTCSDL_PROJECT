"""Keep API requests and the reminder worker out of a database being restored."""
from contextlib import contextmanager

from fastapi import HTTPException
from sqlalchemy import create_engine, text

from app.core.database import database_url

master_engine = create_engine(database_url.set(database="master"), pool_pre_ping=True,
                              isolation_level="AUTOCOMMIT")


@contextmanager
def application_lock(connection, resource, mode="Exclusive", timeout=0):
    result = connection.execute(text("""
        SET NOCOUNT ON;
        DECLARE @result int;
        EXEC @result = sys.sp_getapplock @Resource=:resource, @LockMode=:mode,
             @LockOwner='Session', @LockTimeout=:timeout;
        SELECT @result;
    """), {"resource": resource, "mode": mode, "timeout": timeout}).scalar_one()
    if result < 0:
        raise HTTPException(503, "Database đang có thao tác bảo trì. Vui lòng thử lại sau.",
                            headers={"Retry-After": "15"})
    released = False

    def release():
        nonlocal released
        if not released:
            released = True
            connection.execute(text("EXEC sys.sp_releaseapplock @Resource=:resource, @LockOwner='Session'"),
                               {"resource": resource}).close()

    try:
        yield release
    finally:
        release()


@contextmanager
def database_access():
    with master_engine.connect() as connection:
        with application_lock(connection, f"FamilyConnect:maintenance:{database_url.database}", "Shared") as release:
            yield release
