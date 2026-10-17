# FamilyConnect V10 — thống nhất biểu mẫu và hoàn thiện tương tác

Ngày 17/10/2026. Thực hiện hai việc đầu đã thống nhất: (1) nhất quán biểu mẫu/tên hành động; (2) cảnh báo chưa lưu, truy vấn hai người trên cây và dọn giao diện thừa. Không thực hiện nghiệm thu trình duyệt/điện thoại thật trong lần này.

## Cập nhật
Sao lưu frontend hiện tại. Chép frontend và docs trong ZIP vào thư mục dự án. Từ thư mục chứa frontend chạy:

```powershell
py -m http.server 5500 --directory frontend
```

Mở http://localhost:5500/ rồi Ctrl+F5. Tài khoản mẫu demo / Demo@12345. Giữ nguyên origin/port để tiếp tục dùng dữ liệu đã lưu. Service worker đổi cache fe10 để tải tài nguyên mới; khi dùng PWA có thể cần đóng/mở lại sau khi cập nhật tải xong.

## 1. Một biểu mẫu chỉnh sửa người thân
- Gia đình, Danh bạ và Cây gia phả cùng gọi FamilyDetails.edit(). Mở từ nút Chỉnh sửa hoặc biểu tượng bút trên thẻ danh bạ.
- Biểu mẫu có họ tên, giới tính; các phần ngày sinh/mất, vị trí trong gia phả, liên hệ/học vấn/nghề nghiệp và trạng thái hiển thị được thu gọn.
- Nút ngày sinh/mất mở chính biểu mẫu chung và mở sẵn phần ngày. Không còn một biểu mẫu ngày sinh riêng ở workspace.
- Dữ liệu cũ/thuộc tính mở rộng của thành viên được giữ bằng cập nhật bản ghi hiện có, không thay toàn bộ bằng một bộ trường thiếu.
- Tất cả nơi mở dùng cùng kiểm tra ngày sinh/ngày mất, điện thoại/email, chi nhánh, thế hệ và quan hệ. Lỗi thế hệ hoặc ngày sẽ mở phần liên quan.
- Vai trò họ hàng khác quyền tài khoản. Chỉ quản trị viên gia đình chỉnh sửa dữ liệu phả hệ trong bản mẫu.
- Nút thẻ Danh bạ dùng bút chỉnh sửa thay cho dấu ⋯ nhưng không có menu. Tên người đăng trong ô soạn bài lấy tài khoản hiện tại; nút đăng/sửa bài thể hiện đúng hành động.

## 2. Cảnh báo nội dung chưa lưu
- So sánh trạng thái nhập liệu với lúc mở biểu mẫu; nếu sửa rồi trả về giá trị cũ thì không coi là thay đổi còn chờ lưu.
- Đóng bằng nút Hủy/× hoặc Escape, chuyển gia đình, rời trang hay đổi tab quản trị có biểu mẫu đang sửa sẽ yêu cầu xác nhận khi phù hợp.
- Chọn không bỏ: giữ biểu mẫu và giá trị đang nhập. Chấp nhận bỏ: cho tiếp tục thao tác.
- Trước khi đổi sang biểu mẫu chung khác, kiểm tra nội dung còn chờ lưu, tránh reset mất dữ liệu trước khi hỏi.
- Lưu thành công không hiện nhầm cảnh báo bỏ thay đổi. Form lưu bất đồng bộ của workspace được đánh dấu sạch sau khi lưu xong.
- Cảnh báo native beforeunload do trình duyệt quản lý; trình duyệt có thể yêu cầu tương tác người dùng trước khi cho hiển thị hoặc không cho tùy chỉnh câu chữ.
- Trạng thái chỉ giữ trong RAM do lỗi lưu được cảnh báo khi rời trang. Mở menu, tìm kiếm và truy vấn chỉ đọc không tự làm bẩn biểu mẫu.
- Các bản nháp bình luận đang hiển thị được kiểm tra; khi giao diện dựng lại form, baseline được giữ theo vùng bình luận để không coi bản nháp chưa đăng là nội dung đã lưu.

Đây là cơ chế bảo vệ phía giao diện, không phải tự động lưu mọi bản nháp lên máy chủ. Cần thử hành vi thật trên trình duyệt khi làm bước nghiệm thu tiếp theo.

## 3. Tìm quan hệ giữa hai người
Tại Cây gia phả có khối Tìm quan hệ giữa hai người:
- Chọn hai hồ sơ, đổi vị trí và xem các bước liên kết.
- Tìm đường ngắn nhất trên quan hệ cha mẹ–con/hôn nhân đã nhập. Có thể đi theo hai chiều, diễn giải đúng chiều.
- Hỗ trợ trường hợp cùng hồ sơ, hồ sơ không hợp lệ và chưa có đường nối.
- Không kết luận không có họ hàng chỉ vì dữ liệu chưa đủ; không tự suy đoán cách xưng hô hoặc huyết thống qua quan hệ hôn nhân.
- Không gọi AI, không cần mở trang Trợ lý. Các nút truy vấn nhanh cũ giữ trong phần thu gọn.

## 4. Dọn giao diện và mã cũ
- Xóa HTML/controller của ba biểu mẫu thành viên cũ đã thay thế.
- Xóa giao diện và controller nhắn tin chỉ lưu nháp tại Danh bạ; giữ nguyên dữ liệu bản nháp cũ trong kho, không xóa dữ liệu người dùng.
- Xóa biểu mẫu lời mời nháp không còn đường sử dụng; mời tham gia vẫn đi qua liên kết gia đình V9.
- Xóa hộp thoại sinh nhật cũ ở Cộng đồng; sửa ngày tại hồ sơ.
- Xóa 7 quy tắc CSS riêng cho giao diện lời mời/nháp đã bỏ.
- Bình chọn và kỷ niệm nằm dưới Thêm lựa chọn trong ô soạn bài; chức năng vẫn dùng được.
- Liên kết mạng xã hội của hồ sơ nằm trong phần bổ sung.
- Sửa lời hướng dẫn liên kết tài khoản theo đường dẫn Quản trị → Thành viên & quyền truy cập.

## Kiểm tra
Bộ tests/v10.cjs kiểm tra biểu mẫu chung từ các điểm vào, trường bổ sung được giữ, đóng/đổi biểu mẫu/đổi gia đình khi chưa lưu, cancel/Escape/beforeunload mô phỏng, lưu đồng bộ và bất đồng bộ không hỏi nhầm, chuyển tab cài đặt, truy vấn trực tiếp/ngược/cùng người/thiếu đường và việc xóa biểu mẫu trùng.

Các kiểm tra hồi quy của V8/V9 vẫn có trong frontend/tests; một số test được cập nhật để dùng biểu mẫu chung thay cho ID cũ. Cú pháp JS/CJS, CSS, đường dẫn tệp, ID HTML và phạm vi ZIP được kiểm tra riêng.

Backend 77 tệp và database 20 tệp nguyên byte so với V9. Các lớp API/JWT/SQL Server/AI thật không triển khai trong bản này.

Chưa thực hiện kiểm tra pixel/layout, bàn phím cảm ứng, focus native, giải mã ảnh thật, tải tệp hay PWA trên thiết bị thật. Đây là bước thứ ba đã để sau, không được ghi nhận là hoàn tất bởi test jsdom.
