# Sự kiện gia đình — frontend bước 6

## Cài đặt

Gói cập nhật gồm toàn bộ frontend hiện tại (Tổng quan, Gia đình của tôi, Cây gia phả, Danh bạ, Cộng đồng, Sự kiện); các trang khác vẫn là khung. Sao lưu/commit và đối chiếu phần nhóm tự chỉnh sửa trước khi chép đè.

Chép `frontend` và `docs` vào thư mục gốc `HQTCSDL_PROJECT` và thay thế file cùng đường dẫn. Backend/database không đổi.

```powershell
py -m http.server 5500 --directory frontend
```

Mở http://localhost:5500/pages/events.html và nhấn Ctrl+F5. Giữ cùng địa chỉ/port với các trang khác để dùng chung dữ liệu.

## Đã triển khai

- Banner, bốn ô thống kê, bộ lọc, danh sách sự kiện, lịch tháng, sự kiện nổi bật, nhắc việc, sinh nhật và hoạt động gần đây.
- Tạo/sửa sự kiện: tên, loại, người tổ chức, thời gian bắt đầu/kết thúc, địa điểm, mô tả, ảnh minh họa và đánh dấu nổi bật. Kết thúc phải sau bắt đầu. Có thể nhập sự kiện quá khứ để lưu lịch sử.
- Hủy/mở lại sự kiện; hủy khóa phản hồi và ẩn nhắc việc liên quan, vẫn giữ hồ sơ/album. Xóa có xác nhận và xóa cả phản hồi, nhắc việc, album; không thể hoàn tác.
- Tìm tên/địa điểm không phân biệt dấu, lọc loại/sắp diễn ra/đã đăng ký, sắp xếp ngày. “Đã đăng ký” là phản hồi tham gia, không chứng minh đã có mặt.
- Lịch tháng 42 ô bắt đầu từ thứ Hai, chuyển tháng, về hôm nay, đánh dấu ngày có sự kiện. Chọn ngày để lọc; bấm lại bỏ lọc. Sự kiện nhiều ngày hiện trên mọi ngày giao nhau; nếu kết thúc lúc 00:00 thì không tính ngày kết thúc.
- Tham gia/Quan tâm: tài khoản mẫu chọn lại để bỏ, chọn loại khác để đổi. Sự kiện đã kết thúc hoặc đã hủy khóa phản hồi.
- Xem chi tiết và quản lý phản hồi mẫu của người trong danh sách. Có trạng thái tham gia, quan tâm, không tham gia, được mời. Chưa có đăng nhập/phân quyền thật; mọi chỉnh sửa là mô phỏng trên máy hiện tại.
- Mời thành viên: chọn nhiều người, lưu trạng thái “Được mời · chưa gửi”; không ghi đè phản hồi đã có. Chỉ mời sự kiện chưa kết thúc/chưa hủy. **Không gửi email, thông báo hoặc lời mời qua mạng.**
- Nhắc việc: chọn sự kiện, nội dung, thời hạn, đánh dấu hoàn thành, xóa có xác nhận. Cho phép hạn quá khứ để hiển thị quá hạn. Nhắc việc chỉ xuất hiện trong trang; **chưa có push notification/email/nhắc nền**. Không bắt buộc hạn trước sự kiện vì có thể có việc tổng kết sau sự kiện.
- Album: tối đa 6 ảnh JPG/PNG mỗi sự kiện, tối đa 5 MB/tệp; thu nhỏ cạnh dài tối đa 1.200px và nén JPEG. PNG trong suốt được chuyển nền trắng. Mở ảnh lớn, xóa ảnh có xác nhận; không giữ tệp gốc.
- Xuất `.ics` (iCalendar, tệp lịch): xuất tất cả sự kiện phù hợp bộ lọc chưa hủy, hoặc từng sự kiện từ chi tiết. Tệp tải về để người dùng nhập vào ứng dụng lịch; không tự tạo lịch online/gửi lời mời. Không kèm nhắc việc/album/danh sách người tham gia.
- Sinh nhật đọc trường ngày/tháng đã cập nhật tại Cộng đồng. Không suy đoán ngày sinh từ năm sinh.
- Tổng quan lấy tối đa 3 sự kiện chưa kết thúc, chưa hủy từ cùng dữ liệu; link chi tiết mở trang Sự kiện và đúng gia đình/sự kiện. Hoạt động tĩnh cũ trên Tổng quan vẫn giữ cơ chế cũ.

## Thời gian và số liệu

Mọi thời gian sự kiện/nhắc việc là **giờ Việt Nam (UTC+7)**, không phụ thuộc múi giờ máy. Ngày hiện tại và lịch tháng mặc định cũng theo Việt Nam. Bản xuất `.ics` chuyển giờ sang UTC có hậu tố Z; ví dụ 09:00 Việt Nam → 02:00Z. Dòng dài được gấp theo giới hạn 75 byte UTF-8 của định dạng iCalendar.

Thống kê tính trên toàn gia đình, không phụ thuộc bộ lọc:

- Sắp tới: bắt đầu trong tương lai và chưa hủy.
- Người đăng ký trong tháng: số người khác nhau có phản hồi tham gia ở ít nhất một sự kiện giao với tháng hiện tại, không cộng trùng người giữa các sự kiện. Đây là số đăng ký, không phải điểm danh.
- Nổi bật: sự kiện được đánh dấu, chưa hủy (có thể đã kết thúc).
- Nhắc việc hôm nay: việc chưa hoàn thành, hạn hôm nay, thuộc sự kiện chưa hủy.

Dữ liệu mẫu ban đầu có 4 sự kiện với ngày tương đối quanh lần khởi tạo (một sự kiện đã kết thúc, ba sự kiện sắp tới). Sau khi lưu, ngày mẫu giữ nguyên; không tự dời ngày khi tải lại. Số liệu được tính từ dữ liệu này, không sao chép số minh họa trong ảnh.

## Dữ liệu và file

Gia đình có thêm `eventData: {version: 1, items: [...], reminders: [...]}`; dùng FamilyStore/localStorage hiện có. Không đổi khóa dữ liệu cũ. Lời mời và phản hồi nằm trong `participants`, ảnh trong `album`. Xóa thành viên rồi mở Sự kiện sẽ loại phản hồi của thành viên đó; vẫn giữ tên người tổ chức đã ghi trước đó. Khôi phục gia đình mẫu sẽ xóa dữ liệu sự kiện hiện tại; lần mở sau tạo lại mẫu.

- `frontend/pages/events.html`: bố cục, hộp thoại, biểu mẫu (HTML).
- `frontend/assets/css/events.css`: định dạng và responsive (CSS).
- `frontend/assets/js/modules/events.js`: tương tác, bộ lọc, album, xuất lịch (JavaScript).
- `frontend/assets/js/core/event-store.js`: khởi tạo mẫu, xử lý ngày/giờ, dùng chung với Tổng quan.
- `frontend/pages/dashboard.html` và `frontend/assets/js/modules/dashboard.js`: nạp dữ liệu sự kiện chung và liên kết chi tiết.

Ảnh bìa sử dụng ba hình vẽ minh họa có sẵn từ Cộng đồng; có thể thêm ảnh riêng vào album. Nếu localStorage hết dung lượng hoặc bị chặn, hệ thống báo thay đổi chỉ giữ tạm trong RAM; tải lại sẽ mất phần chưa lưu. Chưa có đồng bộ nhiều thiết bị hoặc hợp nhất khi sửa nhiều tab.

## Kiểm tra

Đã kiểm tra cú pháp, đường dẫn HTML/ID, mô phỏng DOM: tạo/sửa/xóa, ngày kết thúc sai, chuyển UTC+7, sự kiện nhiều ngày kết thúc 00:00, lọc, phản hồi tham gia/quan tâm, lời mời không ghi đè phản hồi, hoàn thành nhắc việc, hủy/mở lại, nội dung và độ dài dòng `.ics`, kiểm tra MIME ảnh, luồng nén ảnh qua mô phỏng Image/canvas, lưu/tải lại, tách hai gia đình, link từ Tổng quan và xóa dữ liệu liên quan.

Chưa kiểm tra bố cục bằng trình duyệt thực tế, ảnh thật, focus native dialog, cảm ứng hoặc nhập `.ics` vào Google Calendar/Outlook thật. Hãy thử trên Chrome/Edge desktop và chiều rộng 390px: chuyển tháng, chọn ngày, tạo sự kiện nhiều ngày, tải ảnh thật, xuất/import lịch và đối chiếu giờ Việt Nam.
