# SCAFFOLD_STATUS — lịch sử phát triển khung → bản mẫu Frontend

> **Để biết trạng thái mới nhất hãy đọc `PROJECT_STATUS.md`.** Tài liệu này giữ lại ý nghĩa của giai đoạn xây dựng bộ khung, không xóa các mốc cũ.

## Bộ khung ban đầu

- Thư mục `backend/` có FastAPI `/health`, các gói routers/services/repositories và TODO.
- `database/` có script tạo cơ sở dữ liệu cùng phần lớn script chưa triển khai.
- `frontend/` bắt đầu từ Dashboard và mở rộng từng trang, sử dụng dữ liệu trình duyệt.
- `tests/` và `docs/` được tạo để có khung kiểm thử và hướng dẫn.

## Các bước Frontend đã có mã ở ZIP hiện tại

Tổng quan → Gia đình → Gia phả → Danh bạ → Cộng đồng → Sự kiện → Di sản → AI mô phỏng → Báo cáo → Thông báo → Hồ sơ → Quản trị. Chi tiết `FRONTEND_FEATURE_MATRIX.md`; đây là **thứ tự phát triển được tài liệu ghi nhận**, không chứng minh ngày hoàn thành từng trang.

Các đợt nâng cấp giao diện tiếp theo gồm: Sidebar dạng icon rail; V3 cải thiện bố cục/Thông báo/Avatar; V4 Đăng nhập/Đăng ký/Menu/Sáng-Tối; V5 sửa tương phản Dark Mode.

## Trạng thái thực sự cần ghi nhớ

- Chưa kết nối nghiệp vụ API/SQL Server; các thao tác hiện chạy với dữ liệu demo trình duyệt.
- Google/Facebook, quên mật khẩu qua email và AI mô hình thực chưa hoạt động.
- Docker/PWA còn khung.
- **Cập nhật V7 (16/10/2026):** `frontend/index.html` đã được sửa để chuyển đến Đăng nhập khi chưa có phiên mẫu, hoặc Tổng quan khi đã có phiên. Nội dung bộ khung cũ được giữ lại để tham khảo lịch sử.
- Kết quả kiểm thử cũ thuộc từng bước lịch sử, không đồng nghĩa tất cả tương tác mới nhất đã PASS.

**Đọc tiếp:** `PROJECT_STATUS.md`, `DEVELOPMENT_HISTORY.md`, `FRONTEND_FEATURE_MATRIX.md`, `DOCUMENT_AUDIT.md`.
