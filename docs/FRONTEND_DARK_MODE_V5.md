# FamilyConnect – Sửa lỗi chế độ tối V5 ( bản update/sửa lỗi v5)

## 1. Lỗi ở phiên bản V4

Khi bật **chế độ tối (Dark Mode)**, màu nền của một số khung chuyển thành xanh đen nhưng các thẻ, nhãn và nút bấm vẫn giữ màu dành cho **chế độ sáng (Light Mode)**. Ví dụ: chữ sáng trên thẻ trắng ở trang Danh bạ, nút lọc có nền trắng và chữ rất nhạt ở trang Sự kiện, nội dung trong bảng Thông báo nổi gần như không đọc được.

Nguyên nhân chính là `frontend/assets/css/theme.css` trước đây chỉ phủ một số bộ chọn CSS và có quy tắc buộc rất nhiều nút kế thừa màu chữ (`button { color: inherit }` với ngoại lệ), khiến màu chữ không phù hợp với nền. Các trang lại có CSS riêng, nhiều nơi dùng giá trị màu cố định như `#fff`.

## 2. Các file thay đổi

| File | Nội dung sửa |
| --- | --- |
| `frontend/assets/css/theme.css` | Bảng màu tối thống nhất và sửa tương phản ở các thành phần chung, Danh bạ, Cộng đồng, Sự kiện, Thông báo, Gia phả, Di sản, AI, Báo cáo và Quản trị. |
| `frontend/assets/js/modules/reports.js` | Trục/nhãn biểu đồ SVG lấy màu từ biến CSS thay vì luôn dùng màu chữ tối của giao diện sáng. |
| `docs/FRONTEND_DARK_MODE_V5.md` | Tài liệu này. |

**Không đổi giao diện sáng, không thay đổi cơ sở dữ liệu hoặc cơ chế lưu dữ liệu, không thêm React/Tailwind.**

## 3. Cách áp dụng trên Windows

1. Sao lưu hoặc commit bản đang hoạt động trước khi thay thế.
2. Giải nén `FamilyConnect_ChiCapNhat_DarkMode_V5.zip`.
3. Sao chép nội dung thư mục `FamilyConnect` bên trong ZIP vào thư mục `FamilyConnect` có sẵn trên máy. Giữ nguyên cấu trúc đường dẫn.
4. Đối chiếu hai file đã thay đổi bằng `git diff`.
5. Trong Terminal tại thư mục `frontend`, chạy: `py -m http.server 5500`.
6. Truy cập `http://localhost:5500/`, đăng nhập tài khoản mẫu, bật chế độ tối từ menu avatar.
7. Nhấn `Ctrl + Shift + R` để tải lại toàn bộ CSS nếu trình duyệt vẫn dùng bộ nhớ đệm cũ.

## 4. Checklist thử nghiệm

- [ ] Giao diện sáng vẫn bình thường sau khi chuyển từ chế độ tối về sáng.
- [ ] Trang Danh bạ: tiêu đề, thông tin trên sáu thẻ thành viên, nhãn thế hệ và các nút đều dễ đọc.
- [ ] Trang Cộng đồng: chữ trong bài đăng, ô tạo bài, bộ lọc và sidebar ảnh/video có độ tương phản phù hợp.
- [ ] Trang Sự kiện: mọi nút lọc (kể cả mục không được chọn), ngày trên lịch, các thẻ sự kiện đều rõ.
- [ ] Thông báo nhỏ: cả tab, văn bản chính, văn bản phụ, nút mở rộng và nút đánh dấu đã đọc đều rõ.
- [ ] Trang Thông báo lớn: đọc/chưa đọc và các nút lọc rõ.
- [ ] Trang Gia phả: tên người, số thế hệ, thanh công cụ và panel người được chọn rõ.
- [ ] Trang Di sản, Trợ lý AI, Báo cáo, Quản trị, Hồ sơ: không còn chữ trắng trên nền trắng.
- [ ] Biểu đồ Báo cáo: nhãn/trục đủ sáng khi bật tối và trở lại màu chữ tối khi bật sáng.
- [ ] Nút chuyển sáng/tối, Sidebar, đăng nhập, đăng xuất vẫn hoạt động.
- [ ] Xem thêm ở màn hình điện thoại và thử F5 để xác nhận trạng thái chủ đề.

## 5. Quy tắc khi lập trình chức năng mới

Không hardcode `background: white` hoặc `color: #fff` cho mọi trạng thái. Dùng biến CSS chung (ví dụ `var(--surface)`, `var(--ink)`, `var(--line)`), hoặc thêm quy tắc vào `theme.css` dành riêng cho `[data-theme="dark"]` khi có màu đặc thù. Khi thiết kế nút có nền xanh đậm, đặt chữ trắng rõ ràng; khi dùng nhãn nền xanh rất nhạt, đặt chữ xanh đậm.

## 6. Giới hạn kiểm tra

Đã kiểm tra cú pháp CSS, cú pháp JavaScript và dùng Chromium dựng một bộ mẫu các thành phần để đo tương phản màu nền/chữ. **Chưa kiểm tra thủ công từng chức năng và từng trạng thái dữ liệu của tất cả trang**; cần kiểm tra trên Cốc Cốc/Chrome trước khi gộp vào `main`.

## Theo dõi sau V5

Dự án đã có CSS vá tương phản V5 nhưng chưa chứng minh tất cả biến thể nút, bảng, dialog, toast, màn hình mobile trên máy người dùng đều đạt. Nếu phát hiện chữ nhạt trên nền sáng/tối, ghi trang + ảnh + kích thước màn hình + trạng thái Sáng/Tối vào GitHub Issue; không ghi “đã xử lý hoàn toàn” chỉ vì file CSS đã có. Theo dõi ở `task-checklist.txt`.
