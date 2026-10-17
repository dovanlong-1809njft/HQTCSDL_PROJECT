# Kiểm chứng bản cập nhật frontend V8

Ngày 17/10/2026. Kiểm tra trực tiếp mã trong bản cập nhật, không chạy SQL Server/backend.

| Kiểm tra | Kết quả |
|---|---|
| Khởi tạo 15 trang với thứ tự script thực tế | PASS trong jsdom |
| Tạo gia đình động, hai tài khoản, gửi yêu cầu, duyệt và liên kết | PASS |
| Tách bài đã lưu, tư liệu yêu thích, hội thoại, thông báo | PASS |
| Chặn sửa dữ liệu quản trị bằng tài khoản thành viên mẫu | PASS các trường hợp được kiểm tra |
| Soạn thông báo, escape nội dung HTML, hiển thị thông báo | PASS |
| Ẩn/khôi phục nội dung có lý do | PASS |
| Thêm hôn nhân, chặn tổ tiên-con cháu, cập nhật ngày sinh | PASS |
| Loading, lỗi tải mô phỏng và thử lại | PASS |
| Revision/xung đột với dữ liệu tab khác | PASS |
| Tạo bài, sự kiện, nhắc việc có chủ sở hữu và tư liệu | PASS |
| Từ chối quan hệ không phù hợp | PASS |
| 12 trang nghiệp vụ với gia đình rỗng và trạng thái dark | PASS trong DOM; không phải kiểm tra pixel |
| Quota localStorage đầy: giữ RAM và trả trạng thái chưa lưu | PASS |
| Đăng ký/đăng nhập bằng Web Crypto, mật khẩu sai, tên trùng | PASS |
| Khóa tài khoản, không biến phiên không hợp lệ thành demo admin | PASS |
| Nhập JSON sai gia đình, phục hồi đúng gia đình | PASS |
| Dữ liệu lưu hỏng không bị tự ghi đè | PASS |
| Thêm bộ minh họa 2 bài/2 tư liệu/2 sự kiện | PASS |
| Cú pháp JavaScript/CJS và phân tích CSS | PASS |
| Liên kết tệp cục bộ/ID HTML không trùng | PASS |
| So sánh backend với ZIP đầu vào | 77 tệp không thay đổi |
| So sánh database với ZIP đầu vào | 20 tệp không thay đổi |

Bộ kiểm tra có trong frontend/tests. Xem README.md tại đó để chạy lại.

## Chưa được kiểm chứng trong môi trường này
- Bố cục thực tế trên Chrome/Edge/Cốc Cốc/Safari và Android/iOS/Windows.
- Kích thước 375/390/768px, thao tác cảm ứng và bàn phím điện thoại.
- Focus và hộp thoại native, clipboard, tải và mở tệp CSV/ICS/JSON/PDF bằng ứng dụng thật.
- Giải mã/nén ảnh bằng canvas với tệp thật.
- Đăng ký service worker, cài đặt PWA và ngoại tuyến trên thiết bị thật. Mã cache chỉ chấp nhận tệp tĩnh trong allowlist; không có API thật trong frontend hiện tại.
- Xác thực/RBAC/JWT/AI/email/push/SQL Server thật: thuộc giai đoạn sau.

Các dòng PASS chỉ áp dụng phạm vi nêu trong bảng. Không dùng kiểm thử jsdom để khẳng định đã nghiệm thu giao diện trên mọi thiết bị.
