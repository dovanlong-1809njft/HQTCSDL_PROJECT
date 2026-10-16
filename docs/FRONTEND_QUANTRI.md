# Quản trị gia đình — frontend mẫu bước 11

## Chạy giao diện
Từ thư mục chứa frontend, chạy `py -m http.server 5500 --directory frontend`.
Mở http://localhost:5500/pages/admin.html và nhấn Ctrl+F5.

## Chức năng
- Tổng quan: số hồ sơ, bài viết, sự kiện, tư liệu lấy từ FamilyStore. Phân hệ chưa khởi tạo hiển thị dấu —, không dùng số tổng giả. Sự kiện bao gồm các mục đã hủy.
- Biểu đồ 30 ngày: bài viết/bình luận theo ngày tạo trong giờ Việt Nam, kèm bảng số liệu. Loại bỏ thời gian thiếu/sai và thời gian tương lai. Không tự tạo dữ liệu thành viên mới vì hồ sơ chưa có ngày tham gia đầy đủ.
- Phân loại bài viết theo trường type. Các phần trăm làm tròn có thể không cộng đúng 100%.
- Thành viên: tìm kiếm, xem thông tin, đánh dấu/bỏ xác minh mẫu có xác nhận. Thêm/sửa/xóa chuyển sang trang Danh bạ.
- Nội dung: mở bài viết chính xác, xóa bài cùng bình luận/phản ứng sau xác nhận. Xóa không thể hoàn tác; tổng bài viết được đồng bộ. Có thể xuất JSON trước khi thao tác.
- Sự kiện: mở chi tiết, hủy/mở lại có xác nhận, giữ nguyên người tham gia và nhắc nhở. Quản lý đầy đủ tại trang Sự kiện.
- Tư liệu: xem chi tiết văn bản và bật/tắt nổi bật; quản lý đầy đủ tại trang Di sản.
- Cài đặt: sửa tên và mô tả gia đình, đồng bộ các trang dùng FamilyStore.
- Nhật ký: ghi thao tác tại trang Quản trị, tối đa 500 mục/gia đình; chưa phải nhật ký kiểm toán đáng tin cậy hay đầy đủ toàn hệ thống.
- Phân quyền mẫu: gán nhãn Thành viên/Kiểm duyệt viên/Quản trị viên cho hồ sơ, không thay đổi vai trò phả hệ và không cấp quyền thật.
- Giao diện: mật độ danh sách gọn/rộng cho trang Quản trị, lưu riêng từng gia đình.
- Xuất JSON chứa gia đình hiện tại (bao gồm dữ liệu module đã khởi tạo và nhật ký), chưa có nhập/khôi phục. Không bao gồm hồ sơ cá nhân lưu riêng, gia đình còn lại hay dữ liệu SQL Server.
- Dung lượng là số byte UTF-8 của JSON gia đình, không phải dung lượng server hay hạn mức trình duyệt.

## Dữ liệu và giới hạn
Toàn bộ là frontend/localStorage. Bất kỳ người dùng trình duyệt nào cũng mở được trang quản trị. Backend phải triển khai xác thực, phân quyền và kiểm tra quyền trên từng API trước khi vận hành thật. Đánh dấu xác minh chỉ là trạng thái mẫu, không xác minh danh tính.
Trang không tự khởi tạo bài viết, sự kiện hay tư liệu mẫu; mở các trang tương ứng để khởi tạo nếu cần. Danh sách thành viên tổng quan là 5 hồ sơ đầu tiên, không gọi là thành viên mới vì chưa có ngày tham gia. Khi đổi gia đình, thao tác xác nhận đang chờ được kiểm tra lại để tránh cập nhật sai gia đình. Nút Làm mới đọc lại dữ liệu lưu bởi tab khác; tránh sửa đồng thời ở nhiều tab.

## Tệp triển khai
- frontend/pages/admin.html: cấu trúc trang.
- frontend/assets/css/admin.css: kiểu dáng và bố cục thích ứng màn hình.
- frontend/assets/js/modules/admin.js: tương tác và xử lý dữ liệu quản trị.

## Kiểm tra
Node kiểm tra cú pháp thành công; jsdom kiểm tra thứ tự script thực tế, không ghi dữ liệu khi chỉ mở trang, xác minh/nhãn vai trò/cài đặt, nội dung HTML an toàn, xóa bài có xác nhận và hủy thao tác, hủy sự kiện, nổi bật tư liệu, chuyển tab, tạo hành động xuất JSON và dữ liệu tách theo gia đình. Kiểm tra liên kết tệp và ID HTML trùng lặp, đối chiếu backend/database không thay đổi. Chưa kiểm tra bố cục trên trình duyệt thật, tải tệp bằng trình duyệt thật hoặc thiết bị di động thật.

Gói có toàn bộ frontend hiện tại và tài liệu. Sao lưu phần nhóm tự chỉnh sửa trước khi chép đè frontend/docs.
