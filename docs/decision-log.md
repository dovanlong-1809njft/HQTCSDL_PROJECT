# Quyết định v2

| Quyết định | Trạng thái / căn cứ |
|---|---|
| Python + FastAPI | Người dùng cho biết nhóm chọn Python; giữ kiến trúc đang có |
| SQL Server/T-SQL, SSMS 22 | Bắt buộc theo yêu cầu người dùng; thay PostgreSQL trong mô tả gốc |
| Web responsive/PWA | Phương án triển khai cho web trên Android/iOS/Windows; chưa đồng nghĩa native |
| Một backend chia module | Đề xuất giữ đơn giản cho 21 ngày |
| 27 bảng dự kiến | Bổ sung session, media links, AI chunks, settings, moderation; chưa phải DDL |
| Giao tác do thủ tục sở hữu | Repository dùng autocommit=True khi gọi các thủ tục này; kiểm thử khi thực hiện |
| Embedding + LLM | Phải có thật để nghiệm thu AI; API key/model chọn khi triển khai |
| Docker và backup/restore | Công việc bắt buộc, không xếp tùy chọn |
| HA thực tế | Chưa triển khai; cần tiêu chí nghiệm thu nếu bắt buộc; restart/backup không phải HA |
| 5 nhóm trách nhiệm A–E | Chưa chốt số người; không mặc định nhóm có 5 thành viên |
| Dòng “Quản lý” thiếu đối tượng | Tạm hiểu quản lý người trong gia phả; là giả định cần làm rõ |

## Các quyết định giao diện đã chốt sau cấu trúc v2 (16/10/2026 theo hội thoại)

| Quyết định | Mức triển khai trong ZIP |
|---|---|
| Không chuyển sang React/Next.js/Framer Motion, giữ HTML/CSS/JavaScript | Có mã phù hợp |
| Sidebar icon rail 3.05rem; hover 15rem; nút ghim; không đẩy nội dung khi hover | Có CSS/JS |
| Cộng đồng: khoảnh khắc hàng riêng, khung tạo bài riêng, feed cuộn một cột, ảnh/video và các bảng phụ | Có mã Frontend mẫu; chưa xác minh realtime từ server |
| Chỉ 2 điểm tới Hồ sơ: mục Sidebar và avatar góc phải; bỏ khối hồ sơ mẫu ở chân sidebar | Có HTML/CSS/JS theo thiết kế mới |
| Thông báo: bấm chuông mở popover, có nút mở rộng vào `notifications.html`, không cần mục Sidebar riêng | Có code |
| Topbar avatar → Xem hồ sơ, Sáng/Tối, Đăng xuất bản mẫu | Có mã; chưa xác thực máy chủ |
| Dark Mode V5 sửa tương phản | Có CSS nhưng cần kiểm thử trực quan toàn bộ |
| `index.html` phải dẫn về Đăng nhập trước | **Đã đồng bộ V7:** chưa có phiên mẫu → `pages/login.html`; đã có phiên mẫu → `pages/dashboard.html`; kiểm thử trình duyệt vẫn cần thực hiện |

Lịch sử chi tiết: `DEVELOPMENT_HISTORY.md`. Bảng chỉ phản ánh trạng thái trong ZIP, không xác nhận đã merge trên GitHub.
