# Cộng đồng — frontend bước 5

## Cập nhật và chạy

Gói ZIP gồm toàn bộ frontend hiện tại: Tổng quan, Gia đình của tôi, Cây gia phả, Danh bạ thành viên, Cộng đồng; các trang khác vẫn là khung giữ chỗ. Sao lưu/commit và đối chiếu phần nhóm tự sửa trước khi chép đè.

Chép `frontend` và `docs` vào thư mục gốc `HQTCSDL_PROJECT`, thay thế file tương ứng. Chưa thay đổi backend hoặc database.

```powershell
py -m http.server 5500 --directory frontend
```

Mở http://localhost:5500/pages/community.html, nhấn Ctrl+F5. Dùng cùng địa chỉ và port với các trang trước để chia sẻ localStorage.

## Chức năng

- Bố cục dựa trên ảnh tham khảo: banner, khoảnh khắc nổi bật, khung tạo bài, bảng tin, ảnh/video, thống kê, chủ đề và sinh nhật.
- Tạo bài viết, bài ảnh, video bằng đường dẫn, kỷ niệm và khảo sát. Nội dung tối đa 3.000 ký tự; tối đa 6 chủ đề, mỗi chủ đề 30 ký tự.
- Tài khoản mẫu cố định: Nguyễn Văn A. Có thể sửa/xóa bài và bình luận do tài khoản mẫu tạo. Đây chỉ là mô phỏng quyền trên giao diện, chưa có xác thực/phân quyền thật.
- Xóa bài có xác nhận; xóa kèm bình luận, cảm xúc và phiếu của bài đó.
- Cảm xúc Thích/Yêu thương: mỗi tài khoản mẫu một cảm xúc trên mỗi bài, chọn lại để bỏ hoặc đổi loại.
- Bình luận tối đa 1.000 ký tự; thêm, sửa, xóa bình luận của tài khoản mẫu. Bản nháp đang gõ được giữ khi tương tác lại bảng tin, nhưng chưa lưu qua tải lại.
- Lưu/bỏ lưu bài; lọc tất cả/bài không có media/ảnh và video/đã lưu; tìm nội dung, tác giả, chủ đề không phân biệt dấu; lọc theo chủ đề; sắp xếp mới nhất/cũ nhất/nhiều tương tác; xem thêm theo từng 6 bài.
- Khảo sát 2–5 lựa chọn khác nhau, tối đa 100 ký tự/lựa chọn. Chọn, đổi hoặc bỏ phiếu. Khi đã có phiếu, giữ nguyên loại bài và lựa chọn, cho sửa nội dung/chủ đề.
- Ảnh: JPG/PNG, tối đa 3 ảnh/bài và 5 MB/tệp; thu nhỏ cạnh dài tối đa 1.200px và nén JPEG trước khi lưu. Ảnh PNG trong suốt có nền trắng khi chuyển sang JPEG. Không giữ nguyên bản ảnh gốc.
- Thư viện ảnh/video: mở từ bài hoặc cột bên cạnh, chuyển trước/sau. Khoảnh khắc nổi bật lấy từ các bài có ảnh, không phải module story tự hết hạn.
- Video: nhận đường dẫn HTTPS trực tiếp tới `.mp4`, `.webm`, `.ogg`; phát bằng trình phát trình duyệt, không tự phát. Không nhận link trang YouTube, không tải tệp video lên. Khả năng phát phụ thuộc codec/trình duyệt và quyền truy cập nguồn. Chỉ lưu URL, không lưu nội dung video. Lúc phát, trình duyệt truy cập máy chủ chứa video.
- Liên kết bài: tạo/copy URL chứa gia đình và mã bài, mở bài tương ứng trên trình duyệt có dữ liệu đó. Nếu clipboard không được phép, ô link được chọn để Ctrl+C. **Đây chưa phải chia sẻ bài cho người khác trên Internet.**
- Sinh nhật: cập nhật ngày/tháng cho thành viên, kiểm tra ngày hợp lệ (chấp nhận 29/2). Không sửa năm sinh trong hồ sơ. Hiện người có sinh nhật trong tháng hiện tại; “Chúc mừng” mở form soạn bài, chưa tự lưu hay gửi bài.

## Dữ liệu và giới hạn

Dùng `FamilyStore` chung; gia đình có thêm `community: {version: 1, posts: [...]}`. Mỗi bài lưu tác giả, loại, nội dung, chủ đề, media, thời gian, cảm xúc, bình luận, trạng thái lưu và khảo sát tùy loại. Thành viên có trường tùy chọn `birthday: {day, month}`; các form cũ giữ trường này khi chỉnh sửa.

Lần đầu mở Cộng đồng của mỗi gia đình, tạo 3 bài minh họa kèm hình vẽ SVG và một vài tương tác mẫu. Không dùng ảnh chân dung thật hoặc suy đoán ngày sinh. Số liệu bên phải lấy từ dữ liệu hiện tại, không sao chép các số tăng trưởng trong ảnh tham khảo.

Sau khởi tạo, trường `family.posts` phản ánh số bài thực tế trong bảng tin mẫu (3 bài ban đầu), thay thế số giả định 18/26 ở phiên bản trước. Tổng quan và Gia đình của tôi đọc cùng số liệu. Lịch sử hoạt động mẫu khác trên dashboard vẫn giữ cách hiển thị của phiên bản trước.

Dữ liệu nằm trong localStorage theo trình duyệt/origin, không gửi đến API/SQL Server. Nếu hết dung lượng/không có quyền lưu, báo rõ thay đổi chỉ giữ trong RAM và sẽ mất khi tải lại. Nhiều bài ảnh có thể làm đầy dung lượng; đây chưa phải cơ chế lưu media sản phẩm thật. Không có đồng bộ đa thiết bị, chat realtime hoặc kiểm duyệt thực tế. Tránh sửa đồng thời nhiều tab; chưa hợp nhất xung đột.

Xóa thành viên không xóa bài/bình luận lịch sử của người đó; nội dung giữ tên tác giả đã ghi lúc tạo. Khôi phục gia đình mẫu ở Gia đình của tôi sẽ xóa dữ liệu cộng đồng đang lưu của gia đình đó; lần mở sau tạo lại 3 bài mẫu.

## File chính

- `frontend/pages/community.html`: nội dung trang, hộp thoại và biểu mẫu (HTML).
- `frontend/assets/css/community.css`: bố cục desktop/mobile, màu sắc và kiểu hiển thị (CSS).
- `frontend/assets/js/modules/community.js`: xử lý tương tác và dữ liệu mẫu (JavaScript).
- `frontend/assets/js/modules/dashboard.js`: dùng số bài đăng thực tế trong FamilyStore.
- `frontend/assets/images/community-gathering.svg`, `community-memory.svg`, `community-travel.svg`: hình vẽ vector minh họa, không phải ảnh gia đình thật.

## Kiểm tra

Đã kiểm tra cú pháp JavaScript và mô phỏng DOM với HTML/JS thực tế: tạo/sửa/xóa bài, lọc/tìm, hiển thị chuỗi HTML an toàn, cảm xúc, bình luận thêm/sửa/xóa, lưu bài, khảo sát và khóa lựa chọn khi có phiếu, kiểm tra loại ảnh/link video, luồng thu nhỏ ảnh bằng mô phỏng Image/canvas, thư viện ảnh, ngày sinh nhật không hợp lệ, soạn lời chúc, dữ liệu sau tải lại, tách dữ liệu hai gia đình, số bài đồng bộ Tổng quan/Gia đình, mở liên kết bài cục bộ. Hồi quy các trang Gia đình, Gia phả, Danh bạ đã đạt.

Chưa xác nhận bố cục bằng trình duyệt thực tế, giải mã/nén ảnh thật, phát video, clipboard thực tế, cảm ứng hoặc focus native dialog. Kiểm tra thủ công Chrome/Edge desktop và chiều rộng 390px: menu, bộ lọc, tạo bài ảnh thật, hủy khi đang xử lý ảnh, phát video HTTPS hợp lệ, mở/đóng thư viện, Tab/Escape, tải lại trang và kiểm tra số liệu các trang.
