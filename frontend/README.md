# Frontend FamilyConnect — giao diện và tương tác mẫu

> **Trạng thái theo ZIP ngày 16/10/2026:** Đã có 14 trang HTML (12 trang ứng dụng + đăng nhập + đăng ký) với nhiều module JavaScript có chức năng mô phỏng. Những trang này **không còn là HTML giữ chỗ**; tuy nhiên chưa phải hệ thống Full-stack thật.

## Xem bằng trình duyệt

```powershell
cd frontend
py -m http.server 5500
```

Mở `http://localhost:5500/`: **chưa có phiên dùng thử** sẽ chuyển thẳng đến `pages/login.html`; **đã có phiên dùng thử** sẽ mở `pages/dashboard.html`. Xem hướng dẫn đăng nhập tại `../docs/FRONTEND_DANGNHAP_TAIKHOAN.md`.

## Những trang đã có mã giao diện

| Trang | Tệp | Tương tác mô phỏng nổi bật |
|---|---|---|
| Tổng quan | `pages/dashboard.html` | Thống kê, hoạt động/sự kiện mẫu |
| Gia đình | `pages/family.html` | Sửa thông tin, thành viên/chi nhánh |
| Cây gia phả | `pages/genealogy.html` | Sơ đồ, lọc, quan hệ, phóng to/thu nhỏ, xuất SVG |
| Danh bạ | `pages/directory.html` | Tìm, lọc, xem thẻ/bảng, xuất CSV |
| Cộng đồng | `pages/community.html` | Bài đăng, bình luận, cảm xúc, khoảnh khắc, album mẫu |
| Sự kiện | `pages/events.html` | Lịch, sự kiện, xác nhận tham gia mẫu, xuất iCalendar |
| Di sản & tư liệu | `pages/heritage.html` | Bộ sưu tập, tư liệu, nội dung/đính kèm minh họa |
| Trợ lý AI | `pages/ai-assistant.html` | Chat và gợi ý mô phỏng JavaScript; **không có LLM thật** |
| Báo cáo | `pages/reports.html` | Biểu đồ, lọc, dữ liệu tổng hợp, CSV/in |
| Thông báo | `pages/notifications.html` | Lọc, đã đọc/chưa đọc, cài đặt mô phỏng |
| Hồ sơ cá nhân | `pages/profile.html` | Chỉnh sửa hồ sơ và avatar lưu cục bộ |
| Quản trị | `pages/admin.html` | Giao diện quản lý mẫu; **không có quyền quản trị máy chủ** |
| Đăng nhập / Đăng ký | `pages/login.html`, `pages/register.html` | Phiên trình duyệt demo; Google/Facebook chưa nối OAuth |

## Thành phần giao diện dùng chung

- `assets/css/sidebar.css` + `assets/js/core/sidebar.js`: Sidebar dạng icon rail 3.05rem → hover 15rem, nút ghim, mobile.
- `assets/css/notification-popover.css` + `assets/js/core/notification-popover.js`: Chuông thông báo mở bảng nổi; nút Mở rộng tới trang thông báo lớn.
- `assets/js/core/profile-badge.js`, `assets/js/core/account-menu.js`: Avatar từ hồ sơ cục bộ; menu Hồ sơ / Sáng–Tối / Đăng xuất.
- `assets/css/theme.css`: Các quy tắc tương phản dành cho chế độ tối (V5).
- `assets/js/core/family-store.js`, `event-store.js`, `notification-store.js`: Dữ liệu mẫu chung lưu trong trình duyệt.

## Cảnh báo và giới hạn

1. `localStorage` không phải CSDL/kiểm soát quyền; **đăng nhập demo không an toàn để triển khai Internet**.
2. Backend/SQL Server chưa kết nối với các trang; dữ liệu không đồng bộ giữa thiết bị.
3. `manifest.json` và `sw.js` có mặt nhưng PWA chưa triển khai đầy đủ.
4. Chế độ tối đã được sửa CSS ở V5 nhưng vẫn cần thử thật từng trang trên Chrome/Cốc Cốc, mobile.
5. Frontend đang dùng HTML/CSS/JS thuần; không tự cài Bootstrap/React/Framer Motion chỉ vì tài liệu kế hoạch cũ đề cập.

## Tài liệu chi tiết

Đọc `../docs/README.md`, `../docs/FRONTEND_FEATURE_MATRIX.md`, `../docs/DEVELOPMENT_HISTORY.md` và các file `FRONTEND_*.md` theo chức năng. Những file hướng dẫn phiên bản cũ là **lịch sử**, không đồng nghĩa mọi kiểm thử vẫn đạt ở bản mới.
# FamilyConnect Frontend V8 — giao diện và nghiệp vụ mẫu

HTML/CSS/JavaScript thuần. Chạy từ thư mục dự án chứa frontend:

```powershell
py -m http.server 5500 --directory frontend
```

Mở http://localhost:5500/ rồi Ctrl+F5. Đăng nhập demo / Demo@12345 hoặc đăng ký tài khoản mẫu. Quản lý gia đình: pages/workspace.html.

- pages: các trang giao diện HTML.
- assets/css: tệp CSS định dạng giao diện, có sáng/tối và kích thước màn hình.
- assets/js/core: xử lý dùng chung như tài khoản, dữ liệu, quyền mẫu và sidebar.
- assets/js/modules: xử lý chức năng từng trang bằng JavaScript.
- assets/images: hình minh họa và icon ứng dụng.
- manifest.json: mô tả cài web app; sw.js: xử lý cache tệp tĩnh PWA.
- tests: kiểm tra DOM bằng jsdom, không cần cài khi chỉ chạy web.

Hướng dẫn thay đổi và kiểm chứng: ../docs/FRONTEND_COMPLETION_V8.md. Trạng thái: ../docs/FRONTEND_VALIDATION_V8.md.

Dữ liệu lưu trên trình duyệt theo origin. Người trong gia phả khác tài khoản đăng nhập. Quyền ở đây chỉ mô phỏng frontend; chưa dùng cho hệ thống thật nhiều người. Backend, SQL Server và AI thật được triển khai ở giai đoạn sau.
