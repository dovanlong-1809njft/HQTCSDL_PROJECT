"""Giả lập bắn Push Notification.

Chưa đấu nối dịch vụ thật (FCM/APNs). Ở bước này chỉ ghi log để kiểm tra
luồng worker chạy đúng. Khi có dịch vụ thật thì thay phần thân hàm send_push.
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

logger = logging.getLogger("worker.push")


def send_push(*, event_id: UUID, reminder_time: datetime) -> None:
    """Gửi một thông báo nhắc sự kiện. Hiện tại chỉ ghi log."""
    logger.info(
        "[PUSH] Nhắc sự kiện %s — hẹn lúc %s",
        event_id,
        reminder_time.strftime("%d/%m/%Y %H:%M"),
    )
