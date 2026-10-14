"""Kết nối SQL Server qua pyodbc

TRẠNG THÁI: KHUNG, CHƯA TRIỂN KHAI.
- Đọc cấu hình từ .env tại gốc dự án, không phụ thuộc thư mục chạy lệnh.
- Một connection cho một đơn vị công việc, đóng đúng hạn; không chia sẻ cursor toàn cục.
- Hợp đồng: autocommit=True khi gọi thủ tục tự quản giao tác; thao tác nhiều bảng nằm trong thủ tục.
- Không gửi GO qua pyodbc. Với driver đồng bộ, dùng endpoint def hoặc threadpool phù hợp.

Đối chiếu docs/api-documentation.md và docs/database-design.md.
Không trả dữ liệu giả như kết quả nghiệp vụ thật.
"""
