"""Lượt quét nhắc nhở sự kiện: lấy các nhắc nhở tới hạn và gửi thông báo.

Dùng lại repository của backend nên câu gọi Stored Procedure chỉ viết một lần.
SP community.usp_ClaimDueReminders dùng UPDLOCK + READPAST, vì vậy chạy nhiều
worker song song cũng không có nhắc nhở nào bị lấy hai lần.
"""

from __future__ import annotations

import logging

from app.core.database import SessionLocal
from app.domains.events import repository

from jobs.push_notification import send_push

logger = logging.getLogger("worker.event_reminder")

BATCH_SIZE = 50


def run_once() -> int:
    """Chạy một lượt. Trả về số nhắc nhở đã xử lý."""
    db = SessionLocal()
    try:
        reminders = repository.claim_due_reminders(db, batch_size=BATCH_SIZE)
    except Exception:
        db.rollback()
        logger.exception("Không lấy được danh sách nhắc nhở.")
        db.close()
        return 0

    if not reminders:
        logger.info("Không có nhắc nhở nào tới hạn.")
        db.close()
        return 0

    sent = 0
    for reminder in reminders:
        reminder_id = reminder["Id"]
        event_id = reminder["EventId"]
        try:
            send_push(event_id=event_id, reminder_time=reminder["ReminderTime"])
            sent += 1
        except Exception:
            # SP đã đánh dấu 'sent' khi lấy ra, gửi hỏng thì trả về 'failed'
            logger.exception("Gửi thông báo hỏng cho nhắc nhở %s.", reminder_id)
            try:
                repository.mark_reminder_failed(db, reminder_id=reminder_id)
            except Exception:
                db.rollback()
                logger.exception("Không cập nhật được trạng thái failed cho %s.", reminder_id)

    logger.info("Đã xử lý %d nhắc nhở, gửi thành công %d.", len(reminders), sent)
    db.close()
    return sent
