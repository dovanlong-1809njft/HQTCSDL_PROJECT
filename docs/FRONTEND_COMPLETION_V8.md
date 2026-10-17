# FamilyConnect — cập nhật frontend V8, ngày 17/10/2026

Đầu vào: FamilyConnect_Frontend (2).zip. Mã nguồn FamilyConnect và HQTCSDL_PROJECT trong ZIP giống nhau ở các tệp dự án đã so sánh; bản cập nhật dùng một thư mục FamilyConnect. Chỉ frontend và tài liệu được chỉnh. Backend và database giữ nguyên từng byte so với đầu vào.

## Cài bản cập nhật
1. Sao lưu thư mục frontend hiện tại và dữ liệu quan trọng trong trình duyệt. Giữ nguyên cách truy cập localhost/port để đọc lại dữ liệu đã lưu.
2. Giải nén, chép frontend và docs vào thư mục dự án chứa backend/database. Gói không chứa backend, database hoặc lịch sử Git.
3. Tại thư mục dự án: `py -m http.server 5500 --directory frontend`.
4. Mở http://localhost:5500/ rồi Ctrl+F5. Giữ nguyên HTML/CSS/JavaScript thuần.
5. Tài khoản quản trị mô phỏng: demo / Demo@12345. Tài khoản mới dùng màn hình Đăng ký; chỉ có hiệu lực tại origin/trình duyệt hiện tại.
6. Mở Quản lý gia đình (workspace.html) để tạo gia đình, xin tham gia, duyệt yêu cầu và thử các luồng mới.

## Những thay đổi chính
| Nhóm | Kết quả trong frontend |
|---|---|
| Danh tính | auth.js chạy trước các module; identity.js cung cấp ID/tên đang đăng nhập. Loại bỏ preview-user cố định trong nghiệp vụ. Nội dung cũ gán preview-user được chuyển sang tài khoản demo khi đọc/ghi, không gán cho người mới. |
| Gia đình | ID động; tạo gia đình rỗng; danh sách gia đình của tôi; khám phá gia đình mẫu trong cùng trình duyệt; nhập mã/liên kết mời; xin tham gia, rút yêu cầu, duyệt/từ chối. |
| Tư cách thành viên | pending/active/rejected/suspended; liên kết tài khoản với người đã có trong cây; không liên kết một người cho hai tài khoản; đổi quyền và tạm khóa/mở tư cách; giữ ít nhất một quản trị viên. |
| Quyền giao diện | Tách quản trị gia đình khỏi quản lý tài khoản toàn bộ bản mẫu; khóa nút thao tác và kiểm tra các thay đổi chính ở kho mẫu. Đây không phải xác thực/phân quyền máy chủ. |
| Dữ liệu riêng | Bài đã lưu, tư liệu yêu thích, hội thoại AI, thông báo đọc/ẩn/cài đặt và các bản nháp theo tài khoản trong từng gia đình. Nhắc việc gắn chủ sở hữu; phản hồi sự kiện giữ theo tài khoản. |
| Hồ sơ phả hệ | Màn hình ngày sinh đầy đủ hoặc chỉ biết năm/ngày-tháng; ngày mất; kiểm tra nhất quán; ngày sinh hồ sơ tài khoản đã liên kết lấy từ hồ sơ phả hệ. |
| Hôn nhân | Thêm/cập nhật ngày bắt đầu/kết thúc và trạng thái; chặn tự kết hôn, trùng cặp và hôn nhân tổ tiên–con cháu. Quan hệ đã kết thúc được chú thích ở bảng/person panel. |
| Thông báo chung | Soạn, xem trước an toàn, sửa và ẩn/hiển thị; xuất hiện trong danh sách thông báo; không gửi qua mạng. |
| Kiểm duyệt | Ẩn/khôi phục bài viết và tư liệu, bắt buộc lý do, lưu lịch sử; nội dung ẩn được lọc khỏi feed, kho ảnh, đề xuất tư liệu, báo cáo và nguồn AI mới. Hội thoại cũ là ảnh chụp văn bản tại thời điểm hỏi, không tự viết lại. |
| Tài khoản | Danh sách tên/email, khóa/mở tài khoản mẫu, không xuất hash/mật khẩu lên bảng; không khóa tài khoản demo quản trị mẫu. |
| Tổng quan | Bỏ hoạt động tĩnh khác nguồn; số liệu dùng cùng FamilyStore. Phân hệ chưa có dữ liệu được khởi tạo rỗng thống nhất, không còn tổng 18/26/8/12 trong khi danh sách trống. |
| Dữ liệu minh họa | Chủ động thêm một bộ 2 bài/2 tư liệu/2 sự kiện tại Bản lưu frontend, có xác nhận, không ghi đè nội dung sẵn có, chặn thêm trùng. Không tự sinh khi mở từng trang. |
| Xung đột | Kiểm tra revision và bản lưu gốc trước khi ghi; chặn bản cũ/khác tab; yêu cầu tải lại. Dữ liệu hỏng không tự bị ghi đè bằng dữ liệu ban đầu. Khi quota đầy, báo chỉ giữ trong RAM. |
| Lớp dữ liệu | api.js cung cấp giao diện bất đồng bộ cho danh sách/lệnh; demo-api.js được dùng cho các luồng workspace để thể hiện loading/error/retry. Các module cũ vẫn có thao tác đồng bộ FamilyStore; đây không phải kết nối API thật. |
| PWA | Manifest có icon 192/512, đăng ký service worker, cache danh sách tệp tĩnh theo allowlist. Không cache API, bản lưu JSON hoặc dữ liệu người dùng; không có push nền. |
| Responsive/accessibility | Bảng cuộn, hộp thoại giới hạn chiều cao viewport, nhóm nút tự xuống dòng, màu các thành phần mới cho dark mode, focus rõ, ảnh lỗi có thay thế, hỗ trợ reduced motion. |

## Quy ước dữ liệu
- USERS/account là tài khoản, FAMILY_MEMBER/member là người trong phả hệ. Vai trò họ hàng không cấp quyền quản trị.
- Hai gia đình mẫu Lê/Nguyễn chỉ có tài khoản demo tham gia mặc định; tài khoản mới bắt đầu chưa có gia đình, có thể xin tham gia hoặc tự tạo.
- Thế hệ vẫn là nhãn tương đối 1–20 do quản trị viên nhập. Cạnh cha mẹ phải đi từ số nhỏ sang số lớn. Không tự tuyên bố suy ra thế hệ tuyệt đối từ đồ thị chưa đầy đủ.
- BirthDate đầy đủ đồng bộ birthYear và birthday. Khi sửa riêng năm/ngày-tháng tại màn hình cũ, ngày đầy đủ không còn phù hợp sẽ bị bỏ để tránh hai giá trị mâu thuẫn. Không tự điền ngày/tháng chưa biết.
- RSVP chuẩn trong frontend: going/interested/declined/invited. Cần ánh xạ với hợp đồng API khi tích hợp sau này.
- Thời gian sự kiện/nhắc việc dùng giờ Việt Nam UTC+7, thời điểm tạo hoạt động dùng ISO có múi giờ. Ngày sinh/mất là ngày lịch.
- Liên kết mời và bản sao dữ liệu hiện chỉ dùng được với các tài khoản trong cùng origin/trình duyệt; chưa phải chia sẻ nhiều thiết bị.
- Bản lưu JSON phục hồi dữ liệu chung của đúng gia đình sau kiểm tra; giữ tư cách thành viên/tài khoản và dữ liệu riêng hiện có. Không dùng bản lưu như migration SQL Server.

## Tệp mới quan trọng
- pages/workspace.html: trang quản lý các luồng bổ sung.
- assets/js/modules/workspace.js: xử lý tương tác quản lý.
- assets/js/core/identity.js: danh tính tài khoản đang dùng.
- assets/js/core/permissions.js: kiểm tra quyền thao tác bản mẫu.
- assets/js/core/data-validation.js: quy tắc ngày/quan hệ/dữ liệu nhập.
- assets/js/core/frontend-shell.js: xử lý dùng chung, picker động, lỗi và xung đột.
- assets/js/core/demo-api.js và api.js: hợp đồng dữ liệu mô phỏng bất đồng bộ.
- assets/css/completion.css: bố cục và trạng thái bổ sung.
- frontend/tests: kiểm tra frontend bằng jsdom, chỉ dùng lúc phát triển.

## Phần cần thử trên trình duyệt thật trước khi tuyên bố nghiệm thu frontend
Không có Chromium trong môi trường kiểm tra lần này. Các kiểm tra DOM không đo được pixel, cảm ứng, bàn phím mobile, focus native dialog, canvas giải mã ảnh thật, tải tệp thật hay cài PWA. Vì vậy bản cập nhật đã có mã và kiểm tra logic, chưa tuyên bố tất cả thiết bị đều đã nghiệm thu.

Thử ở 375/390px, 768px và desktop, sáng/tối:
1. Sidebar hover/ghim/mobile, không che nút bấm; duyệt bằng Tab/Escape.
2. Đăng ký hai tài khoản, đăng nhập/đăng xuất; tạo gia đình và xin/duyệt tham gia.
3. Nhập tên dài, dữ liệu rỗng, tìm không có kết quả; chuyển gia đình trong khi hộp thoại đang mở.
4. JPG/PNG thật, tệp hỏng/sai loại/quá lớn; chọn liên tiếp; đóng hộp thoại trước khi xử lý xong.
5. Tạo/sửa bài, bình luận, phản ứng; tạo sự kiện/RSVP/album; tư liệu/collection và AI mô phỏng.
6. Hai tab cùng sửa: tab cũ bị chặn, tải lại không mất dữ liệu mới.
7. Xuất/nhập JSON, xuất CSV/ICS, in/lưu PDF và kiểm tra ngày giờ.
8. Cài PWA trên trình duyệt hỗ trợ; mở lại sau khi tải tệp tĩnh; kiểm tra offline. Android/iOS/Windows cần kiểm chứng riêng.

## Phạm vi giai đoạn sau
JWT, REST API thật, SQL Server/T-SQL, RBAC backend, email/push, AI/embedding thật, Docker và backup/restore SQL chưa triển khai trong lần này. Không có file backend/database nào bị sửa. PWA là vỏ web cài được khi môi trường hỗ trợ, chưa phải ứng dụng native riêng hoặc bằng chứng đáp ứng mọi yêu cầu mobile của đề tài.
