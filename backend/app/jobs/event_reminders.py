"""Tạo thông báo nhắc lịch

TRẠNG THÁI: KHUNG, CHƯA TRIỂN KHAI.
- Tác vụ chạy một lượt hoặc worker đơn; lịch chạy cấu hình khi triển khai.
- UNIQUE RecipientUserID/EventID/ReminderKey chống tạo trùng khi chạy lại.
- Đọc thời gian UTC; chỉ nhắc sự kiện chưa hủy. Không tự gửi email/SMS.

Đối chiếu docs/api-documentation.md và docs/database-design.md.
Không trả dữ liệu giả như kết quả nghiệp vụ thật.
"""
