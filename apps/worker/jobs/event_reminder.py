"""Dispatch due event reminders to each permitted user inbox atomically."""
import logging
from app.core.database import SessionLocal
from app.core.maintenance import database_access
from app.domains.heritage.repository import execute

logger = logging.getLogger("worker.event_reminder")

def run_once() -> int:
    with database_access():
        with SessionLocal() as db:
            delivered = execute(db, "EXEC community.usp_DeliverDueReminders @BatchSize=50", {}).scalar_one()
            db.commit()
    if delivered:
        logger.info("Dispatched %s inbox notifications", delivered)
    return delivered
