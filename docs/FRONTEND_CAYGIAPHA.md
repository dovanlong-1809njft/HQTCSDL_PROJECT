# Cây gia phả — frontend bước 3

## Cài bản cập nhật

Sao lưu project hoặc commit trước khi chép file. Giải nén gói cập nhật; chép `frontend` và `docs` vào thư mục gốc HQTCSDL_PROJECT, thay thế file cùng đường dẫn. Gói này chứa toàn bộ frontend hiện có (Tổng quan, Gia đình của tôi, Cây gia phả); các trang còn lại vẫn là scaffold. Nếu nhóm đã tự sửa frontend, đối chiếu trước khi ghi đè.

Chạy tại thư mục chứa frontend:

```powershell
py -m http.server 5500 --directory frontend
```

Mở http://localhost:5500/pages/genealogy.html và nhấn Ctrl+F5. Dùng cùng địa chỉ/port với trang Gia đình của tôi để chia sẻ dữ liệu mẫu.

## Thao tác đã triển khai

- Cây theo thế hệ: chọn thẻ để xem hồ sơ, nhãn thế hệ, đường cha mẹ–con và hôn nhân.
- Tìm tên không phân biệt dấu; lọc thế hệ và chi nhánh; đổi hướng dọc/ngang; thu/phóng từ 25–175%; vừa chiều rộng; cuộn xem cây lớn.
- Mặc định sơ đồ hiển thị người có quan hệ; người chưa liên kết nằm trong danh sách mở rộng bên dưới. Khi tìm/lọc, mọi người phù hợp đều được đưa lên sơ đồ; chỉ vẽ liên kết có cả hai đầu đang hiển thị. Khi chưa có liên kết nào, sơ đồ hiển thị toàn bộ thành viên.
- Thêm/sửa thành viên: tên, thế hệ, năm sinh, giới tính, chi nhánh, vai trò, nghề nghiệp, giới thiệu.
- Thêm quan hệ cha/mẹ → con hoặc hôn nhân. Chặn tự liên kết, trùng quan hệ, vòng lặp tổ tiên, cha mẹ ở cùng/sau thế hệ con, năm sinh cha mẹ không trước con (khi có đủ năm sinh), hôn nhân với tổ tiên/con cháu.
- Xóa liên kết cần xác nhận, giữ nguyên hồ sơ thành viên.
- Gợi ý truy vấn: con; anh chị em có ít nhất một cha/mẹ chung; người cùng chi nhánh; thế hệ thứ 3. Truy vấn chạy bằng JavaScript, không phải AI.
- Xuất SVG của phần cây đang hiển thị, độc lập với mức zoom; có thể mở bằng trình duyệt. Không phải bản sao lưu dữ liệu hay xuất PDF.
- Thống kê lấy từ toàn bộ gia đình, không thay đổi theo bộ lọc.

## Dữ liệu và tương thích

Dùng FamilyStore/localStorage chung với Gia đình của tôi và Tổng quan. Không có API/database/backend mới.

Thêm thuộc tính `relations: [{id, type: "parent" | "spouse", from, to}]` vào gia đình; `birthYear` và `gender` là trường tùy chọn của thành viên. Giữ nguyên khóa localStorage/version 1 vì đây là mở rộng tương thích, không thay thế cấu trúc cũ.

Lần đầu đọc dữ liệu chưa có `relations`, tạo một số liên kết **minh họa** giữa các ID gốc của bộ dữ liệu mẫu; không suy diễn quan hệ của thành viên do người dùng mới tạo. Chỉ tạo liên kết cha mẹ–con nếu các ID vẫn tồn tại và thế hệ phù hợp. Quan hệ minh họa không phải thông tin phả hệ thật. Với bộ Lê chưa chỉnh sửa: 32 người, 3 thế hệ, 11 quan hệ, 2 chi nhánh; 10 người có quan hệ xuất hiện trên cây, 22 người ở danh sách chưa liên kết. Số liệu khác ảnh tham khảo vì phản ánh đúng dữ liệu hiện có.

Không tự thêm năm sinh/giới tính vào hồ sơ cũ. Khi thiếu, hiện “Chưa cập nhật”. Avatar mặc định là chữ viết tắt. Thế hệ là trường nhập tay, không tự tính lại từ cây; liên kết hôn nhân không bắt buộc cùng thế hệ và chưa quản lý lịch sử ly hôn/tái hôn.

Sửa thành viên ở Gia đình của tôi giữ các trường mới; sửa thế hệ bị chặn nếu phá quan hệ cha mẹ–con. Xóa thành viên ở Gia đình của tôi xóa kèm liên kết của người đó. Reset gia đình khôi phục dữ liệu mẫu. Các thay đổi chỉ lưu cục bộ; tránh sửa cùng gia đình đồng thời ở nhiều tab (chưa có cơ chế hợp nhất thay đổi).

## File chính

- `frontend/pages/genealogy.html`: bố cục, các hộp thoại.
- `frontend/assets/css/genealogy.css`: cây, panel hồ sơ, responsive.
- `frontend/assets/js/modules/genealogy.js`: tương tác, bố trí SVG/HTML, truy vấn và xuất SVG.
- `frontend/assets/js/core/family-store.js`: bổ sung quan hệ và loại bỏ liên kết tới thành viên bị xóa.
- `frontend/assets/js/modules/family.js`: giữ trường mới và kiểm tra thế hệ khi chỉnh sửa.

## Kiểm tra

Đã kiểm tra cú pháp JavaScript và mô phỏng DOM bằng jsdom với HTML/JS thực tế: tìm/lọc, hướng cây, zoom, thêm/sửa thành viên, thêm/xóa quan hệ, chặn tự thân/trùng/vòng lặp, lưu và tải lại, tách dữ liệu hai gia đình, giữ năm sinh khi sửa ở trang gia đình, xóa liên kết khi xóa người, trạng thái gia đình rỗng, tạo Blob xuất SVG. Kiểm tra hồi quy trang Gia đình của tôi đã đạt.

Chưa kiểm tra bố cục trong trình duyệt thực tế, thao tác cảm ứng, tải file SVG thực tế hoặc focus native dialog. Kiểm tra thủ công Chrome/Edge: màn hình desktop và chiều rộng 390px; menu mobile; đóng dialog bằng Escape; Tab qua các nút; cuộn cây; thêm người → thêm quan hệ → tải lại → xuất SVG và mở file.
