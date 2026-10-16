# Hướng dẫn người dùng — bản mẫu Frontend và mục tiêu ứng dụng

## A. Những gì có thể thử trên Frontend hiện tại

1. Trong thư mục `frontend/`, chạy `py -m http.server 5500`.
2. Mở `http://localhost:5500/pages/login.html`, dùng tài khoản mẫu được ghi ở README gốc. **Không dùng mật khẩu thật**.
3. Chọn gia đình mẫu rồi xem lần lượt: Tổng quan, Gia đình, Cây gia phả, Danh bạ, Cộng đồng, Sự kiện, Di sản, Trợ lý AI, Báo cáo, Hồ sơ, Quản trị.
4. Rê chuột vào Sidebar để mở, thử ghim; bấm chuông ở Topbar để mở Thông báo nhỏ và chọn **Mở rộng** để xem trang lớn.
5. Bấm avatar góc phải → Xem trang cá nhân, đổi Sáng/Tối hoặc Đăng xuất. Mọi thay đổi liên quan hồ sơ/bài viết chỉ là dữ liệu mẫu trong trình duyệt.

**Lưu ý:** Trang gốc `/` trong ZIP hiện chuyển thẳng tới Dashboard, khác với quy trình muốn đăng nhập đầu tiên. Đây là việc cần sửa trong mã nguồn, không phải một tính năng đã hoàn thiện.

## B. Giới hạn của bản mẫu

- Không có xác thực/ủy quyền trên máy chủ và không có dữ liệu SQL Server thật.
- Google/Facebook là nút giao diện chờ tích hợp; Quên mật khẩu chưa gửi email.
- AI chỉ mô phỏng với dữ liệu JS; không phải phản hồi từ mô hình LLM thật.
- Các thao tác lưu dữ liệu localStorage, không chia sẻ giữa thiết bị hoặc trình duyệt.
- Chưa chứng minh PWA và Docker hoạt động đầy đủ.

## C. Mục tiêu sau khi kết nối Backend/Database

Người dùng đăng nhập an toàn, tạo hoặc xin vào gia đình, quản lý thành viên/quan hệ, chia sẻ bài viết, tham gia sự kiện, lưu trữ tư liệu và dùng trợ lý AI trong phạm vi được phân quyền. Người quản trị có API riêng bảo vệ dữ liệu; CSDL có giao tác và kiểm thử đồng thời.

Đọc `requirements.md` và `api-documentation.md` để xem các yêu cầu **dự kiến**, không tự suy ra ứng dụng hiện đã đáp ứng.
