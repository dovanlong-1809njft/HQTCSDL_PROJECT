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
