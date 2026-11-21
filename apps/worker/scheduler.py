"""Run the real inbox every 15 seconds."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import signal
from threading import Event

# Worker dùng lại cấu hình kết nối và repository của backend thay vì tự mở
# kết nối riêng, để chỉ có một nơi khai báo chuỗi kết nối SQL Server.
BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("worker")

def main() -> None:
    # Import sau khi đã nối sys.path tới backend.
    from jobs.event_reminder import run_once
    from jobs.event_completion import run_once as complete_events

    stopped=Event()
    for sig in (signal.SIGINT,signal.SIGTERM):
        signal.signal(sig,lambda *_: stopped.set())
    logger.info('Worker started; inbox checked every 15 seconds')
    while not stopped.is_set():
        try: run_once()
        except Exception: logger.exception('Reminder pass failed; retrying next pass')
        try: complete_events()
        except Exception: logger.exception("Event completion pass failed; retrying next pass")
        stopped.wait(15)


if __name__ == "__main__":
    main()
