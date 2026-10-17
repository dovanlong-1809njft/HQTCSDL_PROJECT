# Cập nhật V10

Biểu mẫu sửa hồ sơ người thân dùng chung ở Gia đình/Danh bạ/Cây. Cây có truy vấn hai người không dùng AI. unsaved.js bảo vệ nội dung chờ lưu. Giao diện nhắn tin nháp và các form trùng đã bỏ. Chi tiết: FRONTEND_V10.md.

# Cập nhật UX V9

Quản trị còn 4 nhóm chính; workspace dùng menu theo ngữ cảnh. Ngày sinh/hôn nhân mở tại hồ sơ/cây. Chi tiết: FRONTEND_UX_V9.md. Các chức năng và giới hạn dữ liệu của V8 giữ nguyên, trừ thay đổi UX được mô tả.

# Ma trận frontend — cập nhật V8

| Phần bổ sung | Mã nguồn | Trạng thái |
|---|---|---|
| Tạo/tham gia/duyệt gia đình | workspace.html, workspace.js | Frontend mẫu; kiểm tra DOM |
| Tài khoản, quyền và liên kết người | identity.js, permissions.js, workspace.js | Quyền UI; chưa có bảo mật backend |
| Ngày sinh/mất, thông tin hôn nhân | data-validation.js, workspace.js | Frontend mẫu |
| Thông báo chung/kiểm duyệt | workspace.js, notification-store.js | Frontend mẫu |
| Dữ liệu cá nhân theo tài khoản | family-store.js | Bản lưu riêng trong từng gia đình |
| Phát hiện xung đột dữ liệu | family-store.js, frontend-shell.js | Kiểm tra revision/bản lưu; chặn ghi đè |
| API mô phỏng | api.js, demo-api.js | Chưa gửi HTTP; module cũ vẫn có truy cập đồng bộ |
| PWA | manifest.json, sw.js, pwa.js | Có mã/icon/cache tĩnh; chưa thử thiết bị thật |
| Kiểm thử | frontend/tests | Các trường hợp trong FRONTEND_VALIDATION_V8.md |

Xem FRONTEND_COMPLETION_V8.md để biết thay đổi, cách chạy và giới hạn.

## Ma trận đầu vào V7 — tham khảo lịch sử

# Ma trận trạng thái các trang Frontend


| Trang | File HTML | File JavaScript nghiệp vụ | Mức hiện tại | Việc ưu tiên khi tích hợp |
|---|---|---|---|---|
| Tổng quan | `dashboard.html` | `dashboard.js` | Giao diện & dữ liệu mẫu | API thống kê/sự kiện |
| Gia đình | `family.html` | `family.js`, `family-store.js` | Thao tác dữ liệu mẫu | Bảng gia đình, thành viên, chi nhánh, quyền |
| Cây gia phả | `genealogy.html` | `genealogy.js` | Sơ đồ/tìm/lọc/thao tác mẫu | Quan hệ phả hệ, tránh vòng lặp, giao tác |
| Danh bạ | `directory.html` | `directory.js` | Tìm/lọc/phân trang mẫu | API tìm kiếm, quyền xem thông tin |
| Cộng đồng | `community.html` | `community.js` | Feed/bình luận/phản ứng mẫu | API bài đăng, media, quyền riêng tư |
| Sự kiện | `events.html` | `events.js`, `event-store.js` | Lịch, tham gia mẫu | API sự kiện, RSVP, tránh trùng |
| Di sản | `heritage.html` | `heritage.js` | Kho tư liệu/album mẫu | File upload, metadata, phân quyền |
| Trợ lý AI | `ai-assistant.html` | `ai.js` | Hội thoại mẫu bằng JS | LLM, retrieval, nguồn dữ liệu được phép |
| Báo cáo | `reports.html` | `reports.js`, `report-math.js` | Biểu đồ/CSV mẫu | SQL View/Procedure, thời gian/nhóm gia đình |
| Thông báo (trang lớn) | `notifications.html` | `notifications.js` | Danh sách/trạng thái mẫu | Thông báo server, phân loại, đọc/chưa đọc |
| Hồ sơ cá nhân | `profile.html` | `account.js` | Chỉnh sửa/ảnh đại diện mẫu | Người dùng thực và quyền riêng tư |
| Quản trị | `admin.html` | `admin.js` | Dashboard quản trị mẫu | RBAC và nghiệp vụ được bảo vệ ở Backend |
| Đăng nhập | `login.html` | `auth-page.js`, `auth.js` | Xác thực mô phỏng trong localStorage | Auth Backend, cookie phiên, rate limit |
| Đăng ký | `register.html` | `auth-page.js`, `auth.js` | Đăng ký mô phỏng | Xác thực thông tin, DB người dùng |

## Chức năng liên trang

| Hệ thống giao diện | Mã nguồn | Thực trạng |
|---|---|---|
| Sidebar | `sidebar.css` / `sidebar.js` | Thu gọn 3.05rem, mở 15rem khi hover; ghim, menu mobile |
| Thông báo nổi | `notification-popover.css` / `notification-popover.js` | Chuông góc phải, bộ lọc, mở rộng trang `notifications.html` |
| Avatar | `profile-badge.js` / `account.js` | Dùng hồ sơ cục bộ; không có tài khoản server |
| Menu tài khoản | `account-menu.css` / `account-menu.js` | Xem hồ sơ, sáng/tối, đăng xuất demo |
| Chế độ tối | `theme.css`, `reports.js` | Đã bổ sung tương phản V5; còn phải kiểm tra trực quan |
| Dữ liệu mẫu | `family-store.js`, `event-store.js`, `notification-store.js` | Chưa đồng bộ nhiều trình duyệt/thiết bị |

## Quy ước nghiệm thu về sau

- **UI sẵn sàng:** trang hiển thị đúng ở Sáng/Tối, 375px/768px/desktop, các nút có xử lý, không lỗi console.
- **API sẵn sàng:** request/response và HTTP status được định nghĩa; backend kiểm tra quyền.
- **Database sẵn sàng:** có bảng, khóa, ràng buộc, transaction/rollback và test chạy trên SQL Server.
- **Hoàn thành chức năng:** một luồng từ UI → API → SQL Server → UI chạy được với dữ liệu thật và có minh chứng kiểm thử.

Chi tiết từng phân hệ: xem các file `FRONTEND_*.md`. Các đề xuất giao diện tham khảo chưa được ghi nhận là chạy code nếu không có file triển khai.
