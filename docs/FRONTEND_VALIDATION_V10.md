# Kiểm chứng V10

- PASS khởi tạo 15 trang theo thứ tự script thực tế trong jsdom.
- PASS biểu mẫu chung từ Gia đình/Danh bạ/Cây, trường học vấn/liên hệ được giữ, không còn các form cũ.
- PASS giữ nội dung khi không đồng ý đóng/chuyển biểu mẫu/đổi gia đình; cancel/Escape/beforeunload mô phỏng.
- PASS lưu đồng bộ và bất đồng bộ không hỏi nhầm bỏ thay đổi; bảo vệ form cài đặt khi đổi tab.
- PASS truy vấn quan hệ trực tiếp, ngược chiều, cùng người, không có hồ sơ và thiếu liên kết; UI hoán đổi hai người.
- PASS hồi quy các luồng V8/V9: hai tài khoản, gia đình, dữ liệu riêng, nội dung/sự kiện/tư liệu, quyền mẫu, kiểm duyệt, bản lưu, quota và xác thực mẫu.
- PASS cú pháp JS/CJS, 20 tệp CSS, liên kết tệp/ID HTML; cập nhật allowlist/cache PWA fe10.
- PASS đối chiếu: 77 tệp backend và 20 tệp database nguyên byte so với V9.

Chưa kiểm thử trên trình duyệt/điện thoại thật, bố cục pixel, native focus, ảnh/canvas, tải tệp và cài PWA. Đây là bước thứ ba, không thuộc hai việc người dùng yêu cầu thực hiện lần này.
