# Di sản & tư liệu — frontend bước 7

## Cập nhật và chạy

Gói chứa toàn bộ frontend hiện tại, bao gồm các trang đã hoàn thành trước và trang Di sản & tư liệu. Các trang khác vẫn là khung giữ chỗ. Sao lưu/commit và đối chiếu phần nhóm tự sửa trước khi chép đè.

Chép `frontend` và `docs` vào gốc `HQTCSDL_PROJECT`, thay thế file cùng đường dẫn. Chưa thay đổi backend/database.

```powershell
py -m http.server 5500 --directory frontend
```

Mở http://localhost:5500/pages/heritage.html, nhấn Ctrl+F5. Dùng cùng địa chỉ/port với các trang khác để chia sẻ dữ liệu trình duyệt.

## Các chức năng

- Bố cục theo ảnh tham khảo: banner, thống kê, các nhóm tư liệu, kho tư liệu, khối nổi bật, dấu mốc, chủ đề, lượt mở và người đóng góp.
- Phân loại: tài liệu lịch sử, câu chuyện gia đình, ảnh tư liệu, người nổi bật, lưu trữ số và kỷ vật.
- Thêm/sửa/xóa tư liệu; nhập tên, năm, bộ sưu tập, người đóng góp, giới thiệu, nội dung, chủ đề, ảnh bìa minh họa, cờ nổi bật/dấu mốc.
- Nội dung tối đa 10.000 ký tự, giới thiệu 500 ký tự, tối đa 6 chủ đề/30 ký tự mỗi chủ đề. Câu chuyện phải có nội dung; ảnh tư liệu phải có ảnh; lưu trữ số phải có tệp; người nổi bật phải liên kết một thành viên đang có; dấu mốc phải có năm.
- Tìm tên, giới thiệu, nội dung, người đóng góp và chủ đề không phân biệt dấu. Lọc loại, bộ sưu tập, yêu thích, nổi bật, chủ đề; sắp xếp mới cập nhật/năm tăng dần/lượt mở. Xem thêm mỗi lần 6 tư liệu.
- Xem chi tiết; yêu thích/bỏ yêu thích. Mỗi lần mở chi tiết tăng một lượt mở mẫu; không tăng khi chỉ chỉnh sửa/lưu yêu thích. Đây là số lượt thao tác cục bộ, không phải thống kê truy cập thật hay người xem duy nhất.
- Quản lý bộ sưu tập: thêm/sửa, kiểm tra trùng tên không phân biệt dấu, xem tư liệu trong bộ sưu tập. Xóa cần xác nhận và **giữ nguyên tư liệu**, chuyển về chưa phân bộ sưu tập.
- Dòng thời gian lấy từ tư liệu có năm và cờ dấu mốc; sắp xếp năm tăng dần, bấm để đọc chi tiết. Đây không phải kết luận lịch sử đã xác minh.
- Người nổi bật liên kết tới hồ sơ thành viên chung để hiện tên/thế hệ/nghề nghiệp. Nếu thành viên bị xóa, tư liệu vẫn giữ, giao diện báo liên kết không còn; khi sửa cần chọn lại thành viên.
- Tải nội dung tư liệu thành `.txt` UTF-8; tải từng tệp đính kèm riêng. Không xuất toàn bộ kho thành bản sao lưu hoặc PDF.

## Tệp đính kèm

Tối đa 3 tệp/tư liệu:

- JPG/PNG: tối đa 5 MB/tệp; thu nhỏ cạnh dài tối đa 1.200px và chuyển sang JPEG. PNG trong suốt chuyển nền trắng. Ảnh được nén, không giữ nguyên tệp gốc; khi tải về dùng đuôi `.jpg`.
- PDF/TXT/DOCX: tối đa 2 MB/tệp; giữ nguyên byte tệp để tải lại.
- Kiểm tra đuôi/MIME và chữ ký sơ bộ PDF/ZIP của DOCX; không phân tích đầy đủ nội dung DOCX/PDF và không có trình quét virus/OCR.
- Không nhận HTML, SVG do người dùng tải lên, file thực thi hoặc tệp ngoài danh sách. SVG minh họa đi kèm dự án là tài nguyên có sẵn.
- Ảnh xem trực tiếp trong hộp thoại. TXT đọc dưới dạng văn bản UTF-8, tối đa 20.000 ký tự ở bản xem trước, không thực thi HTML; tải tệp để đọc đầy đủ hoặc dùng mã hóa khác.
- PDF/DOCX có thông tin tệp và nút tải xuống để mở bằng ứng dụng phù hợp; **chưa có trình đọc PDF/Word trong trang**.
- Khi đang xử lý tệp, khóa lưu. Hủy biểu mẫu sẽ bỏ kết quả đọc tệp đang chờ; không tự tạo tư liệu.

## Dữ liệu chung và giới hạn

Thêm `heritageData: {version: 1, collections: [...], items: [...]}` vào gia đình trong FamilyStore. Không đổi khóa localStorage cũ. Tệp được lưu bằng data URL trong dữ liệu trình duyệt, không tải lên máy chủ.

Lần đầu mở trang mỗi gia đình tạo 5 tư liệu minh họa và 2 bộ sưu tập. Các năm 1920/1978/1995/2000/2024, câu chuyện và hình vẽ đều là mẫu, không phải lịch sử gia đình thật. Thống kê phản ánh dữ liệu đang có, không dùng số 128/356 như ảnh minh họa:

- Tư liệu số hóa: số bản ghi.
- Câu chuyện: số bản ghi loại câu chuyện.
- Ảnh tư liệu: tổng tệp ảnh đính kèm, không đếm ảnh bìa mặc định.
- Người đóng góp: số mã người đóng góp khác nhau, không phải số tài khoản đăng nhập.

Trường `family.heritage` được cập nhật theo số tư liệu thực tế (5 ban đầu), thay số mẫu 8/12 trước đó. Tổng quan và Gia đình của tôi đọc cùng số liệu. Khôi phục gia đình mẫu xóa kho tư liệu hiện tại; lần mở sau khởi tạo lại dữ liệu mẫu.

Tất cả thao tác chỉnh sửa là mô phỏng, chưa có quyền truy cập thật hoặc xác minh nguồn tư liệu. Lưu cục bộ theo trình duyệt/origin; chưa đồng bộ thiết bị, sao lưu máy chủ hay tìm kiếm AI. Nhiều tệp có thể vượt dung lượng localStorage; giao diện báo khi chỉ giữ trong RAM và phần chưa lưu sẽ mất khi tải lại. Tránh sửa đồng thời nhiều tab, chưa hợp nhất thay đổi.

## File chính

- `frontend/pages/heritage.html`: nội dung/bố cục và biểu mẫu (HTML).
- `frontend/assets/css/heritage.css`: kiểu trình bày, bố cục desktop/mobile (CSS).
- `frontend/assets/js/modules/heritage.js`: tương tác, xử lý tệp, bộ sưu tập và lưu dữ liệu mẫu (JavaScript).
- `frontend/assets/images/heritage-archive.svg`: hình vẽ sách, ảnh và thư cũ (SVG/vector).

## Kiểm tra

Đã kiểm tra cú pháp, đường dẫn HTML/ID, cú pháp SVG và mô phỏng DOM: tạo/sửa/xóa, tìm/lọc/yêu thích, dấu mốc, hiển thị chuỗi HTML an toàn, kiểm tra tên bộ sưu tập trùng, xóa bộ sưu tập giữ tư liệu, đọc TXT UTF-8 bằng FileReader thực trong jsdom và đối chiếu byte khi tải, từ chối HTML/PDF sai chữ ký, hủy khi đang đọc tệp, lưu/tải lại, tách hai gia đình, thống kê chung với Tổng quan/Gia đình, trường hợp hết dung lượng và kho rỗng.

Chưa kiểm tra trực quan bằng trình duyệt thực tế, giải mã/nén ảnh thật, mở PDF/DOCX tải về trong ứng dụng thật, cảm ứng hoặc focus native dialog. Kiểm tra thủ công trên Chrome/Edge desktop và chiều rộng 390px: lọc, tạo câu chuyện, tải ảnh/PDF/DOCX hợp lệ, xem/tải lại, đóng form lúc đang đọc tệp, xóa bộ sưu tập và tải lại trang.
