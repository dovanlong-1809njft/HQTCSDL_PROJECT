"""Worker chạy ngầm của phân hệ Cộng đồng & Sự kiện (TV3).

Mỗi phút gọi Stored Procedure community.usp_ClaimDueReminders để lấy các
nhắc nhở đã tới hạn, rồi giả lập bắn Push Notification.

Chạy:
    cd apps/worker
    pip install -r requirements.txt
    python scheduler.py

Dừng bằng Ctrl + C.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler

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

INTERVAL_MINUTES = 1


def main() -> None:
    # Import sau khi đã nối sys.path tới backend.
    from jobs.event_reminder import run_once

    scheduler = BlockingScheduler(timezone="Asia/Ho_Chi_Minh")
    scheduler.add_job(
        run_once,
        trigger="interval",
        minutes=INTERVAL_MINUTES,
        id="claim_due_reminders",
        max_instances=1,      # không chồng lượt khi một lượt chạy lâu
        coalesce=True,        # lỡ nhiều lượt thì gộp lại chạy một lần
        next_run_time=None,
    )
    logger.info("Worker bắt đầu, quét nhắc nhở mỗi %d phút. Ctrl + C để dừng.", INTERVAL_MINUTES)
    run_once()  # chạy ngay một lượt, không chờ hết phút đầu tiên
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker đã dừng.")


if __name__ == "__main__":
    main()
