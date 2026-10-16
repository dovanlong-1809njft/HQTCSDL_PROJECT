# FamilyConnect — Bản update/sửa giao diện V3 sau khi update side bar dẫn đến các lỗi hiện thị cấu trúc giao diện người dùng

## Mục tiêu

Bản sửa trên **FamilyConnect_Frontend(2).zip** do nhóm gửi, sử dụng HTML, CSS, JavaScript thuần. Không chuyển React, không xóa chức năng và không chỉnh code backend/database.

## 1. Cây gia phả

- `frontend/assets/css/genealogy.css`: tự căn giữa `#tree-stage` nếu kích thước sơ đồ nhỏ hơn vùng xem; vẫn có thanh cuộn nếu sơ đồ lớn hơn.
- `frontend/assets/js/modules/genealogy.js`: thêm `ResizeObserver` để tự tính lại phép zoom vừa khung khi khung cây đổi chiều rộng (do kích thước cửa sổ hoặc bảng thông tin).
- Giữ nguyên thao tác tìm kiếm, lọc, quản lý quan hệ, zoom, xuất SVG.

## 2. Hồ sơ cá nhân

- Xóa khối **Hồ sơ mẫu** cuối Sidebar trên 12 trang ứng dụng.
- Giữ **Hồ sơ cá nhân** trong menu bên trái và avatar hình tròn cạnh chuông ở Topbar.
- `frontend/assets/js/core/profile-badge.js` mới: đọc khóa `familyconnect.profile-demo.v1` của localStorage để dùng chung avatar/tên từ trang `profile.html`; khi lưu hồ sơ, event `familyconnect:profile-updated` đồng bộ trên Topbar ngay lập tức.
- Nếu không có ảnh, hiển thị chữ cái viết tắt; ảnh tùy chỉnh của người dùng chỉ lưu trên trình duyệt, chưa phải ảnh tài khoản backend.

## 3. Thông báo

- Xóa mục **Thông báo** khỏi menu Sidebar, **không xóa** `frontend/pages/notifications.html` hoặc chức năng thông báo đầy đủ.
- Nút chuông Topbar giờ mở `notification-popover.js` dạng bảng nổi tại chỗ, **không tự chuyển trang**.
- Bảng nổi lấy dữ liệu trực tiếp từ `NotificationDemo.visible` và `FamilyStore` vốn có, cho phép lọc `Tất cả / Bài viết / Bình luận / Sự kiện / Sinh nhật / Thành viên / Tư liệu / Hệ thống`, lọc Chưa đọc và đánh dấu đã đọc.
- Nút **Mở rộng · Xem toàn bộ thông báo** dẫn đến `notifications.html` để xem chi tiết, tìm kiếm và cài đặt như trước. Đọc thông báo ở cả hai nơi sẽ dùng cùng trạng thái đọc.
- Đây là thông báo **mô phỏng bằng dữ liệu trình duyệt**, chưa phải thông báo thời gian thực từ máy chủ, email hoặc push.

## 4. Nút ghim Sidebar

- `frontend/assets/css/sidebar.css` dời `#sidebar-pin` lên góc trên bên phải của Sidebar, thay vì chiếm một hàng giữa logo và danh mục.
- Giữ lại tính năng hover mở 15rem, thu thành rail 3.05rem, ghim trạng thái và menu mobile.

## Kiểm tra tại máy của bạn

1. Giải nén, đặt file đúng đường dẫn trong thư mục repository đã clone. Sao lưu các file trùng trước khi ghi đè.
2. Tại thư mục `frontend`: `py -m http.server 5500` rồi mở `http://localhost:5500/pages/genealogy.html`.
3. Thu gọn Sidebar, đổi gia đình, lọc thế hệ và bấm **Vừa khung**; cây phải căn giữa khi kích thước cho phép.
4. Vào Hồ sơ cá nhân → **Thay ảnh đại diện**; kiểm tra ảnh hình tròn cạnh chuông và khi chuyển trang/F5.
5. Bấm chuông, chọn từng loại thông báo, chọn **Chưa đọc**, chọn mục, kiểm tra nút **Mở rộng** vào trang thông báo lớn.
6. Hover Sidebar → ghim ở góc trên → chuyển trang → bỏ ghim; kiểm tra cả kích thước điện thoại.
7. Nếu vẫn thấy giao diện cũ, thử `Ctrl+F5` để tải lại CSS/JavaScript.

**Giới hạn xác minh:** Đã kiểm tra tĩnh cấu trúc HTML, cú pháp JavaScript và tính toàn vẹn ZIP; thử nghiệm trình duyệt tự động trong môi trường đóng gói bị chặn truy cập `localhost` nên cần người dùng kiểm tra trực quan trước khi merge lên `main`.
