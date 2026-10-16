# Hồ sơ cá nhân — frontend bước 10

Mở `pages/profile.html` bằng máy chủ tĩnh:

```powershell
py -m http.server 5500 --directory frontend
```

Truy cập http://localhost:5500/pages/profile.html rồi Ctrl+F5.

## Đã triển khai
- Bố cục theo ảnh tham khảo: ảnh bìa, avatar, giới thiệu, liên kết, các tab nội dung và cột gia đình/sự kiện/hoạt động.
- Chỉnh sửa họ tên, lời giới thiệu, ngày sinh, giới tính, quê quán, nơi ở, học vấn, nghề nghiệp, sở thích và liên hệ. Không tự điền thông tin cá nhân từ hình minh họa.
- Liên kết HTTP/HTTPS được kiểm tra; mở tab mới với noopener noreferrer. Nội dung người dùng được escape.
- Đổi ảnh JPG/PNG tối đa 5 MB, giảm kích thước bằng canvas; xóa ảnh trong tab Cài đặt. Ảnh bìa mặc định là nền xanh, không sử dụng ảnh chân dung/phong cảnh trong ảnh mẫu.
- Bài viết, ảnh/video, tư liệu, sự kiện và hoạt động lấy từ FamilyStore, chỉ lọc danh tính mẫu preview-user. Đổi gia đình đổi nội dung liên quan; hồ sơ cá nhân giữ nguyên.
- Khung chia sẻ dẫn đến các trang Cộng đồng, Sự kiện, Di sản đã có chức năng tạo nội dung.
- Hồ sơ lưu riêng tại localStorage `familyconnect.profile-demo.v1`; không chỉnh sửa thành viên phả hệ. Khi hết dung lượng, báo chỉ lưu trong phiên trang.

## Giới hạn rõ ràng
Chưa có tài khoản thật, mật khẩu, xác minh, đăng xuất, phân quyền hoặc liên kết hồ sơ với thành viên phả hệ. Không hiển thị dấu xác minh hay tự dựng quan hệ ông/bà/anh/em. Tên tác giả của nội dung cũ và tên mẫu ở các trang khác không tự đổi theo hồ sơ. Tab khoảnh khắc hiển thị ảnh bài viết, chưa có album cá nhân độc lập. Sự kiện sắp tới chỉ gồm sự kiện bạn tổ chức/đăng ký/quan tâm, chưa hủy và chưa kết thúc. Không có lịch sử RSVP vì dữ liệu hiện tại không lưu thời điểm phản hồi.

## Tệp chính
- frontend/pages/profile.html
- frontend/assets/css/profile.css
- frontend/assets/js/modules/account.js

Gói cập nhật có toàn bộ frontend hiện tại và các tài liệu hướng dẫn. Sao lưu thay đổi riêng trước khi chép đè. Backend/database không có thay đổi.

## Kiểm chứng
Node kiểm tra cú pháp thành công. jsdom kiểm tra tải script thực tế, chỉnh sửa và lưu hồ sơ, xử lý HTML an toàn, chặn URL không hợp lệ, các tab, tách nội dung theo gia đình, lọc đúng tác giả và liên kết bài viết. Kiểm thử hồi quy Thông báo thành công. Chưa kiểm tra trực quan trên trình duyệt thật, hộp thoại hệ điều hành chọn ảnh, canvas xử lý ảnh thật hoặc bố cục trên thiết bị thật.
