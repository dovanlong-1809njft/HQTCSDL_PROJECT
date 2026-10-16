# Báo cáo & thống kê — frontend bước 9

## Cập nhật và chạy

Gói chứa toàn bộ frontend hiện tại và hướng dẫn. Sao lưu/commit, đối chiếu phần nhóm tự chỉnh trước khi chép đè. Chép `frontend` và `docs` vào gốc `HQTCSDL_PROJECT`, thay thế file tương ứng.

```powershell
py -m http.server 5500 --directory frontend
```

Mở http://localhost:5500/pages/reports.html, nhấn Ctrl+F5. Dùng cùng địa chỉ/port với các trang khác để đọc cùng dữ liệu.

## Chức năng

- Chọn gia đình; khoảng ngày gồm năm nay, tháng này, 5 năm gần đây, tùy chọn; bấm Áp dụng sau khi chỉnh ngày. Mỗi báo cáo tối đa 1.830 ngày để biểu đồ dễ đọc. Kỳ đang áp dụng được ghi dưới bộ lọc; thay ngày nhưng chưa áp dụng không đổi dữ liệu xuất/in.
- Làm mới: đọc lại FamilyStore, không tạo dữ liệu nghiệp vụ mới.
- Năm ô tổng quan: thành viên hiện tại, bài viết tạo trong kỳ, sự kiện đã kết thúc trong kỳ, tư liệu tạo trong kỳ, số tham chiếu ảnh/video từ nguồn đã có.
- Biểu đồ hoạt động theo tháng/quý/năm bằng SVG: đường bài viết, cột sự kiện bắt đầu và tư liệu tạo.
- Cơ cấu thế hệ theo toàn bộ thành viên hiện tại; bài cộng đồng theo loại; đóng góp/tổ chức theo thành viên; sự kiện theo loại; tệp đính kèm và loại tư liệu; biểu đồ so sánh các năm trong kỳ.
- Mỗi khối có bảng số liệu tương ứng để đối chiếu, bao gồm toàn bộ thành viên đóng góp khi bấm Xem tất cả.
- Phạm vi & nguồn số liệu: trạng thái các module, trường ngày thiếu/không hợp lệ, cách tính, liên kết đến trang nguồn.
- Xuất CSV UTF-8 có BOM gồm kỳ áp dụng, chỉ số, hoạt động theo tháng, thế hệ, loại bài/sự kiện/tư liệu/tệp và đóng góp. Ô bắt đầu bằng ký tự công thức được thêm dấu nháy đơn. Nếu Excel không tự tách cột, dùng Data → From Text/CSV, chọn dấu phẩy.
- In / Lưu PDF: mở hộp thoại in của trình duyệt, có CSS in để ẩn menu và nút. Người dùng chọn máy in hoặc Save as PDF. **Ứng dụng chưa tự sinh/tải PDF**.

## Quy tắc thống kê

Không sao chép số 28/156/1.240 hoặc tỷ lệ tăng trưởng trong ảnh mẫu. Mọi giá trị tính từ bản ghi đang tồn tại trên trình duyệt.

Thời gian theo Việt Nam (Asia/Ho_Chi_Minh, UTC+7), bao gồm trọn ngày đầu/cuối. Timestamp tạo bài/tư liệu/bình luận phải có múi giờ ISO; ngày giờ sự kiện dùng giờ Việt Nam như trang Sự kiện.

| Chỉ số/biểu đồ | Cơ sở tính |
|---|---|
| Thành viên, thế hệ | Tất cả thành viên hiện tại; không lọc ngày |
| Bài viết | `createdAt` của bài cộng đồng trong kỳ |
| Tư liệu | `createdAt` bản ghi tư liệu trong kỳ; không dùng năm lịch sử `year` |
| Sự kiện đã kết thúc | `end` nằm trong kỳ, không sau thời điểm lập báo cáo, chưa hủy |
| Biểu đồ sự kiện / loại | `start` nằm trong kỳ, chưa hủy; gồm sự kiện tương lai trong kỳ |
| Bài cộng đồng theo loại | Trường `type`, mỗi bài đúng một loại |
| Ảnh/video | Ảnh/link video của bài tạo trong kỳ + ảnh/video đính kèm tư liệu tạo trong kỳ + ảnh album sự kiện bắt đầu trong kỳ, chưa hủy |
| Tệp kho tư liệu | Tệp của tư liệu tạo trong kỳ; ảnh, PDF, TXT, DOCX và loại khác nếu có |
| Đóng góp | Số bài tạo + bình luận tạo + tư liệu tạo + sự kiện tổ chức được tạo trong kỳ; bỏ sự kiện hủy |

Bình luận dùng thời gian của chính bình luận, nên bình luận mới trên bài cũ vẫn được tính. Người tổ chức sự kiện được ghi nhận theo trường organizer; không khẳng định đó là người thao tác tạo. Không cộng phản ứng vì phản ứng hiện chưa có thời điểm riêng.

Ảnh/video đếm số tham chiếu tệp, không khử trùng nội dung và không tính ảnh bìa mặc định. Album sự kiện gắn theo ngày bắt đầu vì chưa có thời gian tải của từng ảnh. PDF/DOCX không được phân tích để đếm ảnh/video bên trong. Sự kiện đã kết thúc theo lịch không chứng minh đã tổ chức hoặc đã điểm danh.

Biểu đồ năm dùng đúng kỳ đã chọn, không tự thêm dữ liệu ngoài kỳ. Không có ngày gia nhập hoặc ảnh chụp dữ liệu thành viên trong quá khứ, nên **không vẽ tăng trưởng thành viên hay tỷ lệ so với năm trước**. Tỷ lệ trên biểu đồ tròn là tỷ trọng hiện tại, được làm tròn.

## Nguồn chưa có dữ liệu và giới hạn

Trang báo cáo đọc `members`, `community.posts`, `eventData.items`, `heritageData.items` qua FamilyStore. Không tự khởi tạo các module chưa mở, không thay đổi dữ liệu nghiệp vụ. Chuyển gia đình chỉ lưu lựa chọn gia đình đang xem như các trang trước.

- Chưa khởi tạo module: chỉ số nguồn đó hiện `—`, bảng/CSV ghi chưa khởi tạo, thông báo có liên kết trang nguồn.
- Module đã khởi tạo nhưng không có bản ghi phù hợp: hiện 0.
- Ảnh/video khi chỉ có một phần nguồn: có dấu `*`, ghi rõ chỉ tính nguồn hiện có.
- Trường thời gian thiếu/sai: bỏ khỏi phép tính theo trường đó và liệt kê tại Phạm vi & nguồn số liệu. Số lỗi là số trường, không nhất thiết là số bản ghi khác nhau.
- Bản ghi bị xóa không còn trong báo cáo, sửa người đóng góp hoặc loại có thể làm kết quả quá khứ thay đổi. Đây chưa phải báo cáo kiểm toán hoặc ảnh chụp lịch sử.
- Dữ liệu chỉ trong trình duyệt/origin, chưa có SQL/API/backend, không đồng bộ nhiều thiết bị. Nếu tab khác thay đổi dữ liệu, bấm Làm mới để đọc lại.

## File chính

- `frontend/pages/reports.html`: bố cục, bộ lọc và hộp thoại (HTML).
- `frontend/assets/css/reports.css`: trình bày, responsive và CSS in.
- `frontend/assets/js/core/report-math.js`: hàm tính ngày/nhóm thời gian/thống kê, chỉ đọc đầu vào.
- `frontend/assets/js/modules/reports.js`: vẽ SVG, bảng dữ liệu, bộ lọc, CSV và in (JavaScript).

Không cần cài Chart.js hay thư viện ngoài. Biểu đồ dùng SVG có tên/tiêu đề và bảng số liệu đối chiếu.

## Kiểm tra

Đã kiểm tra cú pháp, đường dẫn HTML/ID và mô phỏng DOM/tính toán: ranh giới UTC+7, ngày nhuận/ngày sai, nguồn chưa khởi tạo không bị tự tạo, bỏ sự kiện hủy, khác nhau giữa start/end, sự kiện tương lai chưa tính kết thúc, bình luận trên bài cũ, năm lịch sử khác ngày tạo, số media/đóng góp, nhóm tháng/quý/năm, không sửa dữ liệu nguồn, bộ lọc đảo ngày/quá dài, trạng thái rỗng, đổi gia đình, SVG/bảng số liệu, nội dung CSV và chống công thức; gọi hộp thoại in được mô phỏng.

Chưa kiểm tra bố cục bằng trình duyệt thực tế, phân trang bản in/PDF hoặc mở CSV trong Excel thật. Kiểm tra Chrome/Edge desktop và chiều rộng 390px: bộ lọc, làm mới sau chỉnh nguồn ở tab khác, bảng số liệu, xuất CSV, xem trước in và Save as PDF. Dùng dữ liệu có ngày giờ đã biết để đối chiếu.
