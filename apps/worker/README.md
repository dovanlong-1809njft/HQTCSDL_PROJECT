# Worker nền — Nhắc nhở sự kiện (TV3)

Quét bảng `community.EventReminders` mỗi 1 phút và giả lập bắn Push Notification.

## Chạy

```bash
cd apps/worker
pip install -r requirements.txt
pip install -r ../backend/requirements.txt   # worker dùng lại kết nối của backend
python scheduler.py
```

Worker đọc cùng file `.env` với backend (`MSSQL_HOST`, `MSSQL_DB`, `MSSQL_USER`,
`MSSQL_SA_PASSWORD`, `JWT_SECRET_KEY`).

## Cách hoạt động

1. `scheduler.py` dùng APScheduler, đặt lịch chạy `run_once` mỗi phút
   (`max_instances=1` nên không chồng lượt).
2. `jobs/event_reminder.py` gọi `community.usp_ClaimDueReminders`. SP dùng
   `UPDLOCK, READPAST` nên nhiều worker chạy song song không lấy trùng nhắc nhở
   và không phải chờ nhau.
3. SP đổi trạng thái sang `sent` ngay khi lấy ra. Nếu gửi hỏng, worker cập nhật
   lại thành `failed`.
4. `jobs/push_notification.py` hiện chỉ ghi log. Thay thân hàm `send_push` khi
   đấu nối FCM/APNs thật.

## Thử nhanh

Tạo một nhắc nhở đã tới hạn rồi chạy worker:

```sql
INSERT community.EventReminders (EventId, ReminderTime)
VALUES ('<id-su-kien>', DATEADD(MINUTE, -1, SYSUTCDATETIME()));
```
