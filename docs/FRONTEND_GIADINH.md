# Gia đình của tôi - Frontend bước 2 (15/10/2026)

## Cài bản cập nhật
Gói này chỉ chứa các tệp frontend/tài liệu thay đổi so với FamilyConnect_Frontend_Buoc01. Không chứa hoặc sửa backend/database.
Giải nén riêng rồi chép hai thư mục frontend và docs vào gốc repo HQTCSDL_PROJECT, đồng ý thay các tệp cùng tên. Không tạo frontend/frontend. README.md gốc của nhóm được giữ nguyên vì gói không chứa tệp đó.

Tại gốc repo chạy:

```powershell
py -m http.server 5500 --directory frontend
```

Mở http://localhost:5500/pages/family.html. Nếu máy chủ đang chạy, chỉ cần Ctrl+F5. Không cần thư viện frontend, FastAPI hoặc SQL Server cho bước này. Mở HTML trực tiếp có thể xem được nhưng localStorage theo file URL không ổn định giữa các trình duyệt, nên dùng máy chủ tĩnh.

## Đã triển khai
- Bố cục cùng sidebar/topbar với dashboard; nội dung thông tin, thống kê, thành viên nổi bật, chi nhánh, hoạt động và liên hệ theo ảnh minh họa.
- Panel chỉnh sửa bên phải: tên, mô tả/counter 500 ký tự, người đại diện, địa chỉ, điện thoại, email, ngày thành lập. Lưu/Hủy/Escape; dữ liệu chưa lưu không áp dụng.
- Ảnh JPG/PNG tối đa 5 MB, xem trước, xử lý ảnh vuông 320px trong trình duyệt để tiết kiệm lưu trữ, hủy/ảnh mặc định. Ảnh mặc định là chữ viết tắt, không có ảnh stock như minh họa.
- Thêm/sửa/xóa hồ sơ thành viên; chi nhánh, thế hệ, nghề nghiệp, lời nhắn và cờ nổi bật. Hiện tối đa 4 người nổi bật; tổng người nổi bật ghi trên tiêu đề khi nhiều hơn.
- Xem tất cả thành viên, tìm tên không phân biệt dấu, lọc chi nhánh, hồ sơ chi tiết.
- Thêm/sửa/xóa chi nhánh; chặn trùng tên không phân biệt dấu; chặn xóa nhánh còn người. Thành viên chưa phân nhánh vẫn được tính trong tổng gia đình.
- Lịch sử thao tác mẫu, hai gia đình độc lập, khôi phục riêng từng gia đình sau xác nhận.
- Dashboard dùng cùng gia đình đã chọn, tên và số người/thế hệ sau thay đổi. Hoạt động/sự kiện dashboard vẫn là dữ liệu tĩnh bước 1; lịch sử mới của trang gia đình xem tại Gia đình của tôi.

## Các tệp nguồn chính
- frontend/pages/family.html: cấu trúc màn hình và hộp nhập liệu.
- frontend/assets/css/family.css: kiểu dáng riêng, bao gồm drawer và responsive.
- frontend/assets/js/modules/family.js: xử lý thao tác, kiểm tra đầu vào, render bằng textContent.
- frontend/assets/js/core/family-store.js: dữ liệu mẫu và localStorage dùng chung.
- frontend/pages/dashboard.html và assets/js/modules/dashboard.js: nạp store, đồng bộ gia đình và số liệu.
- Các tệp CSS chung và ui.js/main.js được tái sử dụng từ bước 1.

## Dữ liệu và giới hạn
Chỉ dữ liệu giả lập, không có tài khoản/quyền/API hoặc database thật. Vai trò thành viên là mô tả trên giao diện, không phải quyền bảo mật. Lưu cục bộ theo trình duyệt và địa chỉ/cổng: đổi máy, đổi cổng, xóa dữ liệu trình duyệt sẽ không thấy các thay đổi cũ. Khi không lưu được, ứng dụng báo rõ chỉ giữ trong RAM.
Tổng thành viên/chi nhánh/thế hệ được tính từ mảng mẫu; bài đăng/tư liệu là số mẫu vì hai trang đó chưa triển khai.
Xem cây gia phả dẫn tới trang giữ chỗ hiện có; quan hệ cha-con/hôn nhân sẽ được làm ở bước kế tiếp. Tạo gia đình thật, xin tham gia/duyệt tài khoản chưa nằm trong trang này.

## Kiểm tra thực hiện
- JavaScript: node --check đạt; HTML: không trùng ID, script tham chiếu phần tử có thật, liên kết tài nguyên có tệp.
- Node VM chạy family-store.js thật: dữ liệu ban đầu, save/reload, đổi gia đình, reset độc lập, JSON hỏng, storage bị chặn: đạt.
- jsdom chạy HTML/JS thật: sửa/lưu/hủy, điện thoại/email sai, lưu qua reload, thêm/sửa/xóa/tìm thành viên, chống chèn HTML, thêm nhánh/trùng tên/chặn xóa khi còn người/xóa nhánh rỗng, ảnh sai MIME, hai gia đình, đồng bộ dashboard: đạt.
- CHƯA xác minh hiển thị bằng Chromium trong lượt này vì không có browser runtime khả dụng; chưa kiểm tra ảnh decode/resize, focus native của dialog hoặc thiết bị thật. Mô phỏng DOM không thay thế kiểm tra hiển thị.
- Không chạy và không thay đổi backend/database.

## Thử nghiệm nhanh trên máy
1. Đổi gia đình Lê/Nguyễn, đối chiếu số liệu.
2. Mở chỉnh sửa, thay tên/ảnh; Hủy rồi mở lại, sau đó Lưu và tải lại trang.
3. Tạo nhánh mới; thêm người vào nhánh, thử xóa nhánh khi còn người.
4. Tìm người theo tên không dấu, sửa/xóa người; xem thống kê cập nhật.
5. Về Tổng quan rồi quay lại: gia đình và số người đồng bộ.
6. Thử cửa sổ nhỏ/điện thoại và menu; khôi phục mẫu nếu muốn bắt đầu lại.
