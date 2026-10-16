# Danh bạ thành viên — frontend bước 4

## Cập nhật và chạy

Gói ZIP chứa toàn bộ frontend hiện tại (Tổng quan, Gia đình của tôi, Cây gia phả, Danh bạ thành viên), kèm tài liệu cập nhật. Các trang khác vẫn là khung giữ chỗ. Nếu nhóm đã tự sửa frontend, sao lưu/commit và đối chiếu trước khi ghi đè.

Chép thư mục `frontend` và `docs` vào thư mục gốc `HQTCSDL_PROJECT`, thay thế file cùng đường dẫn. Không có file backend/database trong gói này.

```powershell
py -m http.server 5500 --directory frontend
```

Mở http://localhost:5500/pages/directory.html và nhấn Ctrl+F5. Giữ cùng địa chỉ/port với các trang trước để dùng chung dữ liệu mẫu.

## Đã triển khai

- Bố cục theo ảnh tham khảo: tiêu đề, hành động, bộ lọc, bốn ô thống kê, danh sách, bảng thông tin nhanh và gợi ý kết nối.
- Dạng thẻ/dạng bảng; 6 người mỗi trang; chuyển trang; trạng thái không có kết quả.
- Tìm tên, nghề nghiệp, địa điểm/địa chỉ và học vấn không phân biệt dấu. Kết hợp lọc thế hệ, chi nhánh, nghề nghiệp, địa điểm và trạng thái xác minh mẫu.
- Sắp xếp theo toàn bộ họ tên A–Z/Z–A (tiếng Việt), hoặc thế hệ tăng dần. Không tách tên riêng để sắp xếp.
- Thông tin nhanh; hồ sơ đầy đủ gồm liên hệ, học vấn, giới thiệu và các quan hệ đã ghi nhận trong cây gia phả.
- Thêm/sửa/xóa thành viên. Xóa cần xác nhận và loại bỏ liên kết gia phả cùng bản nháp tin nhắn liên quan.
- Form kiểm tra tên, thế hệ, năm sinh, email, số điện thoại; sửa thế hệ/năm sinh không được phá quan hệ cha mẹ–con đang có.
- Xuất CSV UTF-8 có BOM để đọc tiếng Việt. Xuất mọi thành viên phù hợp bộ lọc trên tất cả trang, theo thứ tự sắp xếp hiện tại. Ô chứa ký tự công thức được thêm dấu nháy đơn; số điện thoại cũng được thêm dấu nháy đơn để giữ số 0 đầu khi mở bằng bảng tính. Nếu Excel không tự tách cột, dùng Data → From Text/CSV và chọn dấu phẩy.
- Gợi ý lọc nhanh: chi nhánh đầu tiên, thế hệ 3, giáo viên (khi có), chưa xác minh mẫu. Số lượng lấy từ dữ liệu hiện tại.
- “Mời tham gia”: soạn và lưu bản nháp tên/email/lời nhắn; mở lại từ danh sách. Lưu lại cùng email cập nhật bản nháp tương ứng. **Không gửi email, tạo tài khoản hay tạo liên kết tham gia.**
- “Nhắn tin”: mỗi thành viên một bản nháp nội dung, có thể mở lại để sửa. **Không gửi tin và chưa có chat trực tuyến.**

## Dữ liệu dùng chung

FamilyStore vẫn giữ khóa/version cũ; bổ sung trường tùy chọn cho thành viên: `education` (học vấn), `location` (tỉnh/thành), `address`, `phone`, `email`, `verified` (trạng thái minh họa). `birthYear` và `gender` dùng chung với cây gia phả.

Gia đình có thêm `invitationDrafts` (bản nháp lời mời) và `messageDrafts` (bản nháp tin nhắn). Không có backend/API mới. Khi xóa thành viên ở trang khác, FamilyStore cũng loại bỏ bản nháp tin nhắn liên quan.

Thông tin mới không tự suy đoán từ chi nhánh hoặc tên. Với dữ liệu mẫu cũ, các trường thiếu hiện “Chưa cập nhật”, chưa xác minh; số khu vực ban đầu có thể là 0. Số liệu phản ánh dữ liệu thật đang lưu trên trình duyệt, không sao chép các số minh họa trong ảnh. Avatar dùng chữ viết tắt. “Xác minh” là checkbox mô phỏng, chưa phải xác minh danh tính hoặc phân quyền thật.

Sửa hồ sơ ở Gia đình của tôi hoặc Cây gia phả giữ nguyên các trường bổ sung. Thông tin nhập ở danh bạ xuất hiện ở các trang có hỗ trợ hiển thị trường đó; không phải mọi trang đều trình bày toàn bộ hồ sơ.

Lưu cục bộ theo trình duyệt/origin; tải lại vẫn giữ dữ liệu nếu localStorage được phép. Không dùng dữ liệu cá nhân thật để thử nghiệm. Tránh sửa đồng thời nhiều tab: chưa có cơ chế hợp nhất thay đổi, thông báo yêu cầu tải lại khi tab khác thay đổi dữ liệu.

## File chính

- `frontend/pages/directory.html`: cấu trúc trang và biểu mẫu.
- `frontend/assets/css/directory.css`: định dạng, kiểu thẻ/bảng, responsive.
- `frontend/assets/js/modules/directory.js`: tìm/lọc, phân trang, CRUD, bản nháp và xuất CSV.
- `frontend/assets/js/core/family-store.js`: dữ liệu chung; dọn bản nháp khi xóa người.

HTML là nội dung/bố cục, CSS là kiểu trình bày, JavaScript (.js) là xử lý tương tác; Markdown (.md) là tài liệu hướng dẫn.

## Kiểm tra và giới hạn

Đã kiểm tra cú pháp JavaScript; đường dẫn tài nguyên/ID HTML; mô phỏng DOM bằng jsdom với HTML/JS thực tế: hai kiểu danh sách, phân trang, phối hợp bộ lọc, trạng thái rỗng, thêm/sửa/xóa, kiểm tra email/điện thoại, giữ dữ liệu sau tải lại, tách dữ liệu hai gia đình, bản nháp lời mời/tin nhắn, nội dung CSV và chống công thức, hiển thị an toàn chuỗi HTML, bảo toàn trường khi sửa ở hai trang trước, chặn thế hệ không phù hợp với cây. Kiểm tra hồi quy Gia đình của tôi và Cây gia phả đạt.

Chưa kiểm tra trực quan trong trình duyệt thực tế, focus native dialog, cảm ứng hoặc tải/mở CSV trong Excel thật. Kiểm tra thủ công trên Chrome/Edge ở desktop và chiều rộng 390px: menu, thẻ/bảng, panel thông tin, biểu mẫu, Tab/Escape, chuyển trang, xuất CSV. Trên mobile, panel thông tin nhanh mặc định đóng; chọn “Thông tin” để mở.
