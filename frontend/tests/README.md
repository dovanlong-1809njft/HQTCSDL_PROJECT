# Kiểm thử frontend

Bộ kiểm tra mô phỏng DOM bằng jsdom, không kết nối API/SQL Server.

Tại thư mục frontend/tests chạy `npm install`, sau đó `npm test`. Cần Node.js phù hợp yêu cầu của jsdom 30.1.2. Thư viện kiểm thử không cần khi chạy giao diện bằng máy chủ Python.

Các kiểm tra gồm: tải script của toàn bộ trang, hai tài khoản tham gia/duyệt gia đình, trạng thái riêng của mỗi người, kiểm duyệt, thông báo, hôn nhân, ngày sinh, xung đột cập nhật, tạo bài/sự kiện/tư liệu, gia đình rỗng, chế độ tối, xác thực mẫu bằng Web Crypto và khôi phục bản lưu.

Không thay thế kiểm thử trình duyệt thật: bố cục, cảm ứng, focus, bộ chọn tệp, ảnh/canvas và cài PWA cần thử thủ công.


V9 bổ sung ux-v9.cjs: điều hướng gọn theo vai trò, màn bắt đầu, biểu mẫu thêm người dùng chung, ngày sinh tại chỗ, nhóm quản trị và công cụ chưa hoạt động được ẩn. Hồi quy flows.cjs dùng bộ điều khiển workspace để chọn mục con; kiểm tra này là DOM/module, không phải E2E trình duyệt thật.


V10 bổ sung v10.cjs: biểu mẫu sửa chung, cảnh báo bỏ thay đổi, lưu thành công không hỏi nhầm, bảo vệ tab cài đặt và truy vấn hai người. Xem docs/FRONTEND_V10.md ở gốc dự án. Hộp xác nhận trong test được mô phỏng; không coi đây là kiểm tra hộp thoại trình duyệt thật.
