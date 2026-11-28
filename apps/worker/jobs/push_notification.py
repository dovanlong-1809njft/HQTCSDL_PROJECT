"""Đẩy thông báo ra điện thoại qua Firebase Cloud Messaging (FCM HTTP v1).

Luồng chạy:
  1. community.usp_DeliverDueReminders tạo dòng trong community.Notifications
     (việc này do jobs/event_reminder.py làm).
  2. Job này lấy các thông báo chưa đẩy kèm token thiết bị bằng
     community.usp_ClaimUnpushedNotifications, gửi tới FCM rồi giữ nguyên
     PushedAt nếu gửi được.
  3. Gửi thất bại thì gọi community.usp_ReleaseNotificationPush để lần quét
     sau đẩy lại. Token bị FCM báo không còn hợp lệ thì xóa khỏi bảng.

Cấu hình bằng biến môi trường, đặt trong .env ở gốc repo:
  FCM_SERVICE_ACCOUNT_FILE : đường dẫn tới file JSON service account tải từ
                             Firebase Console (bắt buộc, nếu trống thì job bỏ qua).
  FCM_PROJECT_ID           : mã project Firebase (tùy chọn, mặc định đọc trong
                             file JSON trên).
Chưa cấu hình thì job in một dòng cảnh báo rồi thoát, phần còn lại của worker
vẫn chạy bình thường.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from app.core.database import SessionLocal
from app.core.maintenance import database_access
from app.domains.genealogy.repository import rows
from app.domains.heritage.repository import execute

logger = logging.getLogger("worker.push_notification")

FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
BATCH_SIZE = int(os.getenv("FCM_BATCH_SIZE", "50"))

# Mã lỗi FCM nghĩa là token không còn dùng được: app đã bị xóa hoặc token hết hạn.
DEAD_TOKEN_CODES = {"UNREGISTERED", "INVALID_ARGUMENT", "SENDER_ID_MISMATCH"}

_session = None
_project_id = None
_warned = False


def _authorized_session():
    """Tạo một lần rồi dùng lại; trả về (session, project_id) hoặc (None, None)."""
    global _session, _project_id, _warned
    if _session is not None:
        return _session, _project_id

    path = os.getenv("FCM_SERVICE_ACCOUNT_FILE", "").strip()
    if not path:
        if not _warned:
            _warned = True
            logger.info("Chưa cấu hình FCM_SERVICE_ACCOUNT_FILE; bỏ qua việc đẩy thông báo")
        return None, None

    account_file = Path(path).expanduser()
    if not account_file.is_file():
        if not _warned:
            _warned = True
            logger.warning("Không tìm thấy file service account: %s", account_file)
        return None, None

    try:
        from google.auth.transport.requests import AuthorizedSession
        from google.oauth2 import service_account
    except ImportError:
        if not _warned:
            _warned = True
            logger.warning("Thiếu thư viện google-auth; chạy: pip install -r apps/worker/requirements.txt")
        return None, None

    credentials = service_account.Credentials.from_service_account_file(
        str(account_file), scopes=[FCM_SCOPE]
    )
    project_id = os.getenv("FCM_PROJECT_ID", "").strip()
    if not project_id:
        project_id = json.loads(account_file.read_text(encoding="utf-8")).get("project_id", "")
    if not project_id:
        if not _warned:
            _warned = True
            logger.warning("Không xác định được FCM_PROJECT_ID")
        return None, None

    _session = AuthorizedSession(credentials)
    _project_id = project_id
    logger.info("Đã cấu hình FCM cho project %s", project_id)
    return _session, _project_id


def _send(session, project_id: str, item: dict) -> tuple[bool, str]:
    """Gửi một thông báo tới một thiết bị. Trả về (thành công, mã lỗi FCM)."""
    message = {
        "message": {
            "token": item["Token"],
            "notification": {"title": item["Title"], "body": item["Body"]},
            # Để app điều hướng tới đúng sự kiện khi người dùng bấm vào thông báo.
            "data": {
                "notification_id": str(item["NotificationId"]),
                "event_id": str(item["EventId"]) if item["EventId"] else "",
            },
            "android": {"priority": "high"},
        }
    }
    url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    response = session.post(url, json=message, timeout=15)
    if response.status_code < 300:
        return True, ""

    detail = ""
    try:
        body = response.json().get("error", {})
        detail = body.get("status", "") or body.get("message", "")
        for info in body.get("details", []):
            if info.get("errorCode"):
                detail = info["errorCode"]
                break
    except ValueError:
        detail = response.text[:200]
    return False, detail


def run_once() -> int:
    """Một lượt quét. Trả về số thông báo đã đẩy được tới ít nhất một thiết bị."""
    session, project_id = _authorized_session()
    if session is None:
        return 0

    with database_access():
        with SessionLocal() as db:
            pending = rows(
                db,
                "EXEC community.usp_ClaimUnpushedNotifications @BatchSize=:batch_size",
                batch_size=BATCH_SIZE,
            )
            # Commit ngay để chốt việc đã nhận: tiến trình nền khác không lấy lại.
            db.commit()

            if not pending:
                return 0

            failed_ids: set[str] = set()
            sent_ids: set[str] = set()
            dead_tokens: set[str] = set()

            for item in pending:
                notification_id = str(item["NotificationId"])
                try:
                    ok, code = _send(session, project_id, item)
                except Exception:
                    logger.exception("Lỗi khi gọi FCM cho thông báo %s", notification_id)
                    failed_ids.add(notification_id)
                    continue

                if ok:
                    sent_ids.add(notification_id)
                elif code in DEAD_TOKEN_CODES:
                    # Thiết bị không còn nhận được: xóa token, không đẩy lại.
                    dead_tokens.add(item["Token"])
                    logger.info("Xóa token hết hiệu lực (%s)", code)
                else:
                    logger.warning("FCM từ chối thông báo %s: %s", notification_id, code)
                    failed_ids.add(notification_id)

            for token in dead_tokens:
                execute(
                    db,
                    "EXEC community.usp_DeleteDeviceToken @Token=:token",
                    dict(token=token),
                ).close()

            # Chỉ trả lại các thông báo không gửi được tới bất kỳ thiết bị nào.
            retry = sorted(failed_ids - sent_ids)
            if retry:
                execute(
                    db,
                    "EXEC community.usp_ReleaseNotificationPush @IdsJson=:ids",
                    dict(ids=json.dumps(retry)),
                ).close()

            db.commit()

    if sent_ids:
        logger.info("Đã đẩy %s thông báo ra thiết bị", len(sent_ids))
    return len(sent_ids)
