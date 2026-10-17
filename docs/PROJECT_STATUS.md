# Cập nhật mới nhất — frontend V10

Hoàn thành hai nhóm công việc đã thống nhất: biểu mẫu chỉnh sửa người thân dùng chung/tên hành động; cảnh báo chưa lưu, truy vấn quan hệ hai người và dọn giao diện/mã trùng. Xem FRONTEND_V10.md. Chưa thực hiện nghiệm thu trình duyệt/điện thoại thật. Backend/database giữ nguyên. Nội dung V9/V8 dưới đây là lịch sử.

# Cập nhật mới nhất — frontend V9

Đã tinh gọn điều hướng, gom khu quản trị, bổ sung hướng dẫn bắt đầu và biểu mẫu người thân/ngày sinh/hôn nhân tại chỗ. Xem FRONTEND_UX_V9.md. Backend/database giữ nguyên. Ghi chú V8 bên dưới là lịch sử.

# Trạng thái mới nhất — frontend V8 ngày 17/10/2026

Bản cập nhật hiện tại sửa frontend trên FamilyConnect_Frontend (2).zip. Chi tiết mới nhất: FRONTEND_COMPLETION_V8.md và FRONTEND_VALIDATION_V8.md. Các ghi chú V7 dưới đây là lịch sử của đầu vào; khi khác nhau, dùng hai tài liệu V8.

Đã bổ sung workspace.html và các luồng tạo/tham gia/duyệt gia đình, liên kết tài khoản, hôn nhân, thông báo chung, kiểm duyệt, quyền UI, dữ liệu riêng và bản lưu frontend. Bổ sung manifest/icon/service worker cho PWA tĩnh; chưa kiểm chứng cài trên thiết bị thật. Toàn bộ backend/database vẫn nguyên trạng khung như đầu vào, không được triển khai trong lần cập nhật này.

## Lịch sử đầu vào

# Trạng thái dự án FamilyConnect — chụp tại ZIP ngày 16/10/2026

## Tóm tắt theo mức độ hoàn thành

| Hạng mục | Mức độ được xác nhận | Bằng chứng cụ thể | Còn thiếu / lưu ý |
|---|---|---|---|
| Cấu trúc dự án | **Có file** | Các thư mục frontend/backend/database/docs/tests/scripts/.github | Không đồng nghĩa đã lập trình hoàn thiện |
| 12 trang ứng dụng | **Có HTML + mã JS tương tác mẫu** | `frontend/pages/` + `assets/js/modules/` | Chưa xác nhận kiểm thử E2E với SQL Server |
| Đăng nhập/đăng ký | **Mô phỏng trình duyệt** | `login.html`, `register.html`, `auth.js`, `auth-page.js` | Không có xác thực Backend, Google/Facebook OAuth, email quên mật khẩu |
| Lối vào `/` | **Đã sửa ở bản V7** | `frontend/index.html` nạp `auth.js`, kiểm tra phiên mẫu và điều hướng | Chưa có phiên → Đăng nhập; đã có phiên → Tổng quan. **Chưa phải xác thực Backend** |
| Sidebar chung | **Có mã** | `sidebar.css`, `sidebar.js`, HTML trên 12 trang | Cần thử UX/thiết bị thật |
| Thông báo nhỏ | **Có mã** | `notification-popover.css/js`, `notification-store.js` | Thông báo chỉ dùng dữ liệu mô phỏng, chưa push/email thật |
| Avatar/menu tài khoản | **Có mã** | `account-menu.css/js`, `profile-badge.js`, `account.js` | Chưa liên kết tài khoản máy chủ |
| Sáng/Tối | **Có quy tắc V5** | `theme.css`, `reports.js`, `FRONTEND_DARK_MODE_V5.md` | Cần kiểm tra toàn bộ màu chữ/nền trên Cốc Cốc/Chrome |
| API Backend | **Khung ban đầu** | `backend/app/main.py` trả `/health` | Hầu hết router/service/repository chưa có nghiệp vụ thực |
| SQL Server | **DDL chưa triển khai** | `database/01_create_database.sql`; các script khác đa phần TODO | Chưa có DB/bảng/transactions chạy thật từ ZIP |
| AI | **Mô phỏng UI** | `frontend/assets/js/modules/ai.js` | Chưa tích hợp mô hình AI/embedding/kiểm soát dữ liệu thật |
| PWA / Docker | **Mức khung** | `manifest.json`, `sw.js`, Dockerfile, compose | Chưa chứng minh cài đặt và vận hành thực |
| Test | **Có các file kế hoạch/khung** | `tests/*.py`, `database/tests/*.sql` | Không ghi nhận là đã PASS kiểm thử thực tế |

## Những điểm cần làm rõ với nhóm ngay

1. **Kiểm thử lối vào web app (V7):** đã sửa `index.html` theo luồng V4, cần xác nhận trực tiếp trên trình duyệt trường hợp chưa đăng nhập, đang có phiên và sau khi đăng xuất. Phiên vẫn chỉ là bản mẫu localStorage.
2. **Chốt tiêu chí nghiệm thu:** HTML có nút và dữ liệu mẫu ≠ có API/SQL Server thật. Cần ghi minh chứng từng tầng khi báo cáo môn học.
3. **Chốt kế hoạch frontend → database → backend:** Frontend giúp hình dung; trước khi chia nhóm cần thiết kế từ điển dữ liệu, ERD và hợp đồng API.
4. **Chốt phần nào bắt buộc:** AI, PWA, Docker, sao lưu/khôi phục, HA phải đối chiếu đề bài giảng viên; không đánh dấu hoàn tất do đã có tên file.
5. **Tài liệu định hướng khác tài liệu trạng thái:** `requirements.md`, `database-design.md`, `api-documentation.md` mô tả mục tiêu/chưa triển khai và không thay thế bằng chứng code.

## Dữ liệu mẫu và an toàn

- Tài khoản demo công khai chỉ để dùng trong `localhost`.
- Nhiều tính năng lưu `localStorage` theo trình duyệt và origin; không chia sẻ cùng lúc giữa các thành viên.
- Không nhập dữ liệu riêng tư hoặc mật khẩu thật vào bản demo; không cam kết tài khoản tách biệt/an toàn.
- Không dùng `GET /health` làm bằng chứng kết nối SQL Server: mã ghi `database: not_checked`.

## Kết luận cho thành viên mới

**Đang ở giai đoạn bản mẫu Frontend + chuẩn bị thiết kế Database/Backend**. Hãy chạy Frontend và đọc các tài liệu trước khi phân chia việc theo file; đừng tự cho rằng API hoặc CSDL đã tồn tại chỉ vì có cây thư mục.

## Phụ lục cập nhật — Index điều hướng V7 (16/10/2026)

- Bản chụp trạng thái ban đầu của tài liệu trên vẫn dựa vào `FamilyConnect_Frontend(3).zip`.
- Theo yêu cầu bổ sung, chỉ `frontend/index.html` được sửa ở lớp ứng dụng: bỏ meta refresh vào Dashboard, dùng `FamilyDemoAuth.getSession()` của `frontend/assets/js/core/auth.js` để chọn Login hoặc Dashboard.
- Các API, CSDL và phương án xác thực thật **chưa triển khai**. Trạng thái hoạt động trên Cốc Cốc/Chrome cần người dùng kiểm thử.
