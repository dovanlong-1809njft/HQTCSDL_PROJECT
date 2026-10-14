# Kiến trúc v2

Một ứng dụng nguyên khối chia mô-đun (modular monolith): frontend HTML/CSS/JS + FastAPI + SQL Server. Không thêm React, Django, Flutter hoặc database thứ hai vào phạm vi hiện tại.

## Luồng xử lý
Trình duyệt gửi HTTPS/JSON đến router; Pydantic kiểm tra dữ liệu; dependency kiểm tra phiên/quyền; service điều phối; repository gọi T-SQL có tham số hoặc stored procedure qua pyodbc. SQL Server giữ dữ liệu chuẩn. SSMS là công cụ quản trị, không phải tầng trung gian của ứng dụng.

## Vị trí chức năng
- routers: URL và HTTP; schemas: cấu trúc request/response.
- services: nghiệp vụ; repositories: truy vấn; db: kết nối.
- core: JWT, quyền và lỗi; integrations: LLM/embedding.
- jobs/event_reminders.py: nhắc lịch chạy nền, cơ chế chống trùng trong CSDL.
- media_service: lưu tệp ngoài thư mục công khai, metadata và các liên kết trong SQL.
- search_service: retrieval theo quyền, cosine similarity; ai_service dùng nguồn đã lọc.
- report_service: CSV; dashboard_service dùng số liệu SQL.

## Giao tác và tài nguyên
Thủ tục sở hữu transaction nghiệp vụ nhiều bảng; pyodbc autocommit=True khi gọi thủ tục theo hợp đồng. Không chia sẻ cursor/connection toàn cục. pyodbc là driver đồng bộ nên tránh chạy truy vấn chặn trực tiếp trong async def; dùng def hoặc threadpool phù hợp.
Chống SQL injection bằng tham số ?. Tên cột sort/order phải chọn từ whitelist, không nhận chuỗi SQL từ frontend. GO chỉ dùng trong SSMS/sqlcmd.

## Triển khai mục tiêu
FastAPI phục vụ frontend cùng origin, API /api/v1. main.py hiện chỉ /health, chưa mount static và routers.
Docker phải có backend, cấu hình worker nếu dùng, dữ liệu upload bền vững. SQL Server có thể là instance trên máy hoặc container phù hợp. Khi đưa lên Internet cần HTTPS. Chưa có HA thực tế.

## Di động
PWA là web dùng trên các hệ điều hành; manifest/icons/service worker và thử thiết bị thuộc kế hoạch bàn giao. Không cache dữ liệu gia đình riêng tư. Chưa có app native/APK/IPA.

## Bảo mật dữ liệu AI
Lọc quyền trước retrieval, không để mô hình tự chọn family_id hoặc chạy SQL tùy ý. Quan hệ được tính bằng logic có thể kiểm thử rồi mới diễn giải. Tóm tắt và đề xuất đều trả nguồn hoặc lý do. Dữ liệu demo giả lập, khóa API chỉ ở server.
