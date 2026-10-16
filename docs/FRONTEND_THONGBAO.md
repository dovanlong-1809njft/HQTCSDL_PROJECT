# Thông báo — frontend 

## Cập nhật và chạy

Gói ZIP gồm toàn bộ frontend hiện tại và tài liệu. Sao lưu/commit và đối chiếu phần nhóm tự sửa trước khi chép đè. Chép `frontend` và `docs` vào gốc `HQTCSDL_PROJECT`, thay thế file cùng đường dẫn.

```powershell
py -m http.server 5500 --directory frontend
```

Mở http://localhost:5500/pages/notifications.html, nhấn Ctrl+F5. Dùng cùng địa chỉ/port với các trang khác để đọc cùng dữ liệu.

## Đã triển khai

- Bố cục theo ảnh tham khảo: tiêu đề, bộ lọc loại, danh sách theo nhóm thời gian, cột bộ lọc nhanh, thao tác đọc/ẩn và cài đặt.
- Lọc tất cả, bài viết, bình luận, sự kiện, sinh nhật, thành viên, tư liệu, hệ thống; tìm nội dung không phân biệt dấu; chỉ xem chưa đọc; xem thêm mỗi lần 20 thông báo.
- Nhóm Hôm nay, Hôm qua, Tuần này, Trước đó, Sắp tới theo dữ liệu và Không rõ thời gian. Ngày/giờ hiển thị theo Việt Nam UTC+7; nhóm Tuần này bắt đầu thứ Hai.
- Mở chi tiết tự đánh dấu đã đọc; có thể chuyển lại chưa đọc. Đánh dấu tất cả áp dụng mọi thông báo thuộc các loại đang bật, không chỉ kết quả tìm kiếm; thông báo đang ẩn không bị đổi trạng thái. Đánh dấu theo loại cần chọn một loại trên hàng bộ lọc.
- Ẩn từng thông báo hoặc các thông báo đã đọc có xác nhận. Không xóa nội dung nguồn. Khôi phục thông báo đã ẩn giữ trạng thái đọc cũ.
- Bộ lọc nhanh hiện tổng số thông báo đang bật theo loại; huy hiệu ở tab là số chưa đọc. Huy hiệu ở menu trái/chuông đầu trang dùng chung trạng thái trên các trang đã triển khai.
- Cài đặt bật/tắt loại thông báo chỉ điều khiển hiển thị và huy hiệu; không xóa dữ liệu. Bật lại loại sẽ thấy lại thông báo và trạng thái cũ.
- Tùy chọn email/trình duyệt **chỉ lưu lựa chọn**. Không gửi email, gọi API thông báo, yêu cầu quyền trình duyệt hoặc tạo thông báo hệ điều hành.
- Giờ yên tĩnh theo Việt Nam: hỗ trợ khoảng qua nửa đêm (ví dụ 22:00–07:00), gồm giờ bắt đầu và không gồm giờ kết thúc. Khoảng bắt đầu/kết thúc bằng nhau bị từ chối. Trong giờ này chỉ ẩn huy hiệu đếm; danh sách vẫn đọc được. Chưa có âm thanh/thông báo đẩy cần tắt.
- Sinh nhật hôm nay có nút soạn lời chúc theo mẫu, sao chép hoặc mở Cộng đồng. Không tự đăng/gửi. Nếu clipboard bị chặn, ô văn bản được chọn để Ctrl+C.
- Làm mới đọc lại bản dữ liệu đã lưu trên trình duyệt (có thể do tab khác thay đổi), rồi tính lại danh sách. Nếu phần mới chỉ nằm trong RAM vì không lưu được, không thay nó bằng bản cũ trên đĩa.

## Nguồn thông báo

Không tạo thêm người hoặc tương tác giả theo ảnh minh họa. Danh sách được dựng từ dữ liệu đang có:

| Nguồn | Thông báo |
|---|---|
| `community.posts` | Bài tạo mới, lần sửa gần nhất và bình luận theo thời điểm trong dữ liệu |
| `eventData.items` | Hồ sơ sự kiện theo ngày tạo, mô tả trạng thái hiện tại |
| `eventData.reminders` | Việc đến hạn, chưa xong, sự kiện chưa hủy |
| `heritageData.items` | Tư liệu theo ngày tạo bản ghi |
| `members[].birthday` | Sinh nhật đúng ngày/tháng hiện tại, không suy đoán từ năm sinh |
| `activities` | Hoạt động thành viên/gia phả/hệ thống và nguồn dự phòng khi module chi tiết chưa có |

Để tránh lặp, khi nguồn Cộng đồng/Sự kiện/Di sản đã khởi tạo thì nhật ký tương ứng không dùng thêm để dựng thông báo. Các lần sửa bài hiện chỉ giữ mốc sửa gần nhất, không có toàn bộ lịch sử phiên bản. Sự kiện dùng mã ổn định: sửa trạng thái/nội dung phản ánh trong thông báo đang có, không tự tạo một thông báo mới cho mọi thay đổi. Không tạo thông báo cảm xúc vì dữ liệu cảm xúc hiện chưa có thời gian riêng.

Phạm vi là bảng cập nhật gia đình cho tài khoản mẫu, chưa có hộp thư riêng theo người nhận/quyền truy cập. Có thể thấy thao tác của chính tài khoản mẫu. Thời gian hiển thị theo nguồn, không phải bằng chứng đã nhận thông báo từ máy chủ. Nguồn thiếu thời gian hiện Không rõ thời gian.

Dữ liệu mẫu cũ thường có 3 dòng hoạt động; số thực tế thay đổi theo dữ liệu các module đang có, không cố định bằng 3 như ảnh. Bản ghi nguồn bị xóa thì thông báo dựng từ bản ghi đó không còn. Trạng thái đọc/ẩn giữ theo mã ổn định; khôi phục thông báo đã ẩn chỉ khôi phục nguồn còn tồn tại.

Liên kết bài/sự kiện mở đúng mã và gia đình; bình luận mở về bài chứa bình luận. Hồ sơ/tư liệu hiện trực tiếp nội dung nguồn trong hộp thoại, có liên kết mở trang Danh bạ/Di sản chung (chưa có định vị chi tiết bằng URL tại hai trang đó). Nhật ký không có mã nguồn cụ thể chỉ liên kết trang chức năng, không đoán bản ghi.

## Dữ liệu và phần dùng chung

Gia đình có trường tùy chọn:

```text
notificationData:
  version: 1
  readIds: [mã thông báo đã đọc]
  hiddenIds: [mã thông báo đã ẩn]
  preferences:
    types: các loại đang bật
    email / browser: lựa chọn kênh chưa kết nối
    quiet: enabled, start, end
```

Mở trang hoặc tính huy hiệu không tự ghi trạng thái/khởi tạo nguồn nghiệp vụ. Chỉ thao tác đọc/ẩn/cài đặt mới lưu metadata qua FamilyStore. Trạng thái và cài đặt tách riêng cho hai gia đình. Reset gia đình mẫu xóa cả trạng thái/cài đặt thông báo.

FamilyStore có thêm sự kiện nội bộ `familyconnect:change` sau lưu/chuyển gia đình để huy hiệu trên trang hiện tại cập nhật. `refresh()` kiểm tra bản lưu trước khi đọc lại và giữ phần RAM nếu trước đó trình duyệt báo không ghi được. Các trang đã triển khai nạp `notification-store.js` sau `family-store.js`; không cần cài thư viện.

Huy hiệu và danh sách tính lại mỗi phút khi trang đang mở. Không chạy nền khi đóng trang, không có realtime từ máy chủ. Với tab khác, thông báo yêu cầu bấm Làm mới hoặc tải lại; chưa có hợp nhất thay đổi đồng thời. Không tự xóa dữ liệu khác để giải phóng dung lượng. Nếu localStorage bị chặn/đầy, trạng thái mới giữ tạm trong RAM và giao diện báo rõ.

## File chính

- `frontend/pages/notifications.html`: cấu trúc trang/hộp thoại (HTML).
- `frontend/assets/css/notifications.css`: định dạng desktop/mobile (CSS).
- `frontend/assets/js/modules/notifications.js`: lọc, trạng thái, chi tiết và cài đặt (JavaScript).
- `frontend/assets/js/core/notification-store.js`: dựng thông báo, cài đặt mặc định, giờ yên tĩnh, huy hiệu dùng chung.
- `frontend/assets/js/core/family-store.js`: phát sự kiện thay đổi nội bộ và đọc lại bản lưu.
- `frontend/assets/css/main.css`: kiểu huy hiệu; các trang đã triển khai nạp thêm script dùng chung.

Backend/database không thay đổi.

## Kiểm tra

Đã kiểm tra cú pháp và mô phỏng DOM với HTML/JS thật: danh sách gốc, lọc, đọc/chưa đọc, theo loại, ẩn/khôi phục, trạng thái qua tải lại và tách gia đình; cài đặt loại/kênh, giờ yên tĩnh qua nửa đêm và biên giờ; thông báo bài/bình luận/sự kiện/tư liệu/sinh nhật/nhắc việc; chuỗi HTML an toàn; link nguồn đúng; lời chúc chưa gửi; đọc lại dữ liệu thay đổi ở bản lưu; hết dung lượng giữ trạng thái RAM.

Kiểm tra nạp **đúng các script trong HTML** ở toàn bộ trang đã triển khai để xác nhận huy hiệu và sự kiện lưu không gây vòng lặp/lỗi phụ thuộc. Các kiểm tra hồi quy chức năng Gia đình/Gia phả/Danh bạ/Cộng đồng/Sự kiện/Di sản/Trợ lý/Báo cáo đều đạt sau thay đổi FamilyStore.

Chưa kiểm tra bố cục bằng trình duyệt thực tế, focus native dialog, thao tác cảm ứng hoặc clipboard hệ điều hành. Không có dịch vụ gửi để kiểm thử email/push. Hãy thử Chrome/Edge desktop và chiều rộng 390px: bộ lọc, đọc/ẩn/khôi phục, đổi gia đình, giờ yên tĩnh, huy hiệu khi chuyển trang, thêm nội dung ở tab khác rồi Làm mới và mở link chi tiết.
