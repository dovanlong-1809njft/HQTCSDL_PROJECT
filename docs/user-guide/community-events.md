# Hướng dẫn sử dụng — Cộng đồng & Sự kiện

Phân hệ do TV3 phụ trách. Tài liệu dành cho người dùng cuối và cho người chấm khi cần dò lại từng chức năng trên giao diện.

Tài liệu liên quan: [đặc tả yêu cầu](../requirements/community-events.md), [đặc tả API](../api-spec/community-events.md).

## 1. Vào hệ thống

| Nền tảng | Địa chỉ | Ghi chú |
| --- | --- | --- |
| Web | `http://localhost:5173` | Đăng nhập tại `/login`. |
| Mobile (Flutter) | Chạy `flutter run` trong `apps/mobile` | Máy ảo Android cần đổi địa chỉ API thành `10.0.2.2:8000` thay cho `localhost`. |

Backend phải chạy trước: `python -m uvicorn app.main:app --port 8000` trong `apps/backend`, với SQL Server đang bật.

Màn hình của phân hệ này:

| Chức năng | Web | Mobile |
| --- | --- | --- |
| Bảng tin, bình luận, cảm xúc, báo cáo | `/community` | tab Cộng đồng (`lib/community.dart`) |
| Lịch sự kiện, RSVP, thư viện ảnh | `/events` | tab Lịch (`lib/calendar.dart`) |
| Nhắc nhở sự kiện | `/events` | tab Nhắc nhở (`lib/reminders.dart`) |

Mọi chức năng dưới đây chỉ hiển thị dữ liệu của gia đình mà tài khoản có hồ sơ gia phả. Tài khoản `admin` xem được mọi gia đình. Nếu bảng tin trống dù đã có dữ liệu, nguyên nhân thường là tài khoản chưa được liên kết vào gia đình nào — xem mục 6.

## 2. Bảng tin

**Xem bảng tin.** Mở `/community`. Mỗi bài hiển thị tên người đăng, nội dung, thời điểm đăng, ảnh kèm theo, số bình luận và số cảm xúc.

**Đăng bài kèm ảnh.** Nhập nội dung, chọn ảnh rồi bấm đăng. Bài và toàn bộ ảnh được lưu cùng lúc. Nếu có lỗi ở giữa, hệ thống không lưu bài nào thay vì lưu một bài thiếu ảnh. Nội dung để trống thì hệ thống từ chối.

**Bình luận.** Mở một bài rồi nhập bình luận. Bình luận của mình có thể sửa hoặc xóa.

**Bày tỏ cảm xúc.** Chọn một trong sáu loại: Thích, Yêu thích, Haha, Wow, Buồn, Tức. Mỗi người chỉ có một cảm xúc trên mỗi bài: chọn loại khác thì cảm xúc cũ được đổi sang loại mới, bấm lại đúng loại đang chọn thì gỡ cảm xúc.

**Báo cáo nội dung.** Chọn báo cáo trên bài, bình luận hoặc ảnh, nhập lý do. Khi một nội dung nhận đủ 3 báo cáo chưa xử lý, hệ thống tự ghi một dòng nhật ký để quản trị viên xem xét. Người báo cáo không thấy gì khác biệt, đây là việc xử lý nội bộ.

## 3. Sự kiện

**Xem lịch tháng.** Mở `/events`. Lịch hiện các sự kiện trong tháng kèm số người đã nhận tham gia. Chuyển tháng bằng nút điều hướng. Sự kiện lúc 23:59 ngày cuối tháng vẫn nằm trong tháng đó.

**Tạo sự kiện.** Nhập tiêu đề, thời gian bắt đầu, thời gian kết thúc và địa điểm. Tiêu đề không được để trống. Quyền tạo và sửa sự kiện thuộc trưởng họ và quản trị viên.

**Trả lời tham gia.** Chọn Tham gia, Có thể hoặc Không tham gia. Đổi câu trả lời bao nhiêu lần cũng được, hệ thống chỉ giữ câu trả lời mới nhất. Chỉ câu trả lời Tham gia được tính vào số người tham dự.

**Thư viện ảnh.** Mở một sự kiện để xem ảnh, thêm ảnh hoặc xóa ảnh mình đã tải lên.

## 4. Nhắc nhở sự kiện

Đặt nhắc nhở cho một sự kiện bằng cách chọn thời điểm muốn được nhắc. Tiến trình nền quét định kỳ và gửi thông báo khi đến hạn, sau đó nhắc nhở chuyển sang trạng thái đã gửi. Mỗi nhắc nhở chỉ gửi một lần, kể cả khi hệ thống chạy nhiều tiến trình nền song song. Nhắc nhở chưa đến hạn có thể hủy.

Tiến trình nền nằm ở `apps/worker`. Nếu không nhận được nhắc nhở, kiểm tra tiến trình này đã chạy chưa.

## 5. Thông báo

Thông báo của phân hệ gồm nhắc nhở sự kiện đến hạn và bài viết dạng thông báo của gia đình. Xem tại `/notifications` trên web.

## 6. Khi gặp sự cố

| Hiện tượng | Nguyên nhân thường gặp | Cách xử lý |
| --- | --- | --- |
| Bảng tin và lịch trống dù đã có dữ liệu | Tài khoản chưa có hồ sơ gia phả thuộc gia đình nào | Nhờ quản trị viên liên kết tài khoản vào một thành viên gia phả, hoặc đăng nhập bằng tài khoản `admin` |
| Báo lỗi không có quyền khi đăng bài | Đăng vào gia đình mà mình không thuộc, hoặc đăng bài thông báo khi không phải trưởng họ | Chọn đúng gia đình, hoặc nhờ trưởng họ đăng |
| Đăng bài kèm ảnh báo lỗi dữ liệu ảnh | Danh sách ảnh gửi lên không đúng định dạng JSON | Chọn lại ảnh và gửi lại; nếu gọi API trực tiếp thì kiểm tra `media` theo mẫu trong đặc tả API |
| Không nhận được nhắc nhở | Tiến trình nền chưa chạy | Chạy `apps/worker` theo hướng dẫn trong `apps/worker/README.md` |
| Mobile không gọi được API | Máy ảo không hiểu `localhost` | Đổi địa chỉ API sang `10.0.2.2:8000`; máy thật thì dùng địa chỉ IP của máy chạy backend |
| Web gọi API báo lỗi xác thực | Token hết hạn | Đăng xuất rồi đăng nhập lại |
