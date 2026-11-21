"""Send event completion inbox entries in bounded, concurrency-safe SQL batches."""
import logging
from app.core.database import SessionLocal
from app.domains.heritage.repository import execute

logger = logging.getLogger("worker.event_completion")


def run_once():
    with SessionLocal() as db:
        delivered=execute(db,"EXEC community.usp_DeliverEndedEvents @BatchSize=50",{}).scalar_one()
        db.commit()
    if delivered:
        logger.info("Delivered %s event completion notifications",delivered)
    return delivered
