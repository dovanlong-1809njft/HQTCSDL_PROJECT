"""Chạy đúng một lượt quét rồi thoát.

Dùng cho nơi không giữ được tiến trình chạy liên tục, ví dụ GitHub Actions gọi
theo lịch. Khác với scheduler.py là vòng lặp vô hạn 15 giây một lượt.

    cd apps/worker && python run_once.py

Cần các biến môi trường kết nối SQL Server giống backend (MSSQL_HOST,
MSSQL_PORT, MSSQL_DB, MSSQL_USER, MSSQL_SA_PASSWORD, JWT_SECRET_KEY), và
FCM_SERVICE_ACCOUNT_FILE nếu muốn đẩy thông báo ra điện thoại.
Lỗi sẽ làm tiến trình thoát với mã khác 0 để lịch chạy báo đỏ, dễ phát hiện.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("worker.run_once")


def main() -> None:
    from jobs.event_completion import run_once as complete_events
    from jobs.event_reminder import run_once as deliver_reminders
    from jobs.push_notification import run_once as push_notifications

    delivered = deliver_reminders()
    complete_events()
    pushed = push_notifications()
    logger.info("Xong một lượt: %s thông báo vào hộp thư, %s đẩy ra thiết bị", delivered, pushed)


if __name__ == "__main__":
    main()
