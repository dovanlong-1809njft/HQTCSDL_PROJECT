# Hợp đồng API v2 — thiết kế, chưa triển khai

Tiền tố /api/v1. main.py hiện CHỈ có GET /health ngoài tiền tố này. Các dòng GET/POST là các phương thức riêng trên cùng URL, không phải một tên phương thức ghép.

| Router (.py) | Phương thức | Đường dẫn sau /api/v1 | Chức năng | Quyền |
|---|---|---|---|---|
| auth | POST | /auth/register | Tạo tài khoản | Guest |
| auth | POST | /auth/login | Đăng nhập, tạo phiên và JWT | Guest |
| auth | POST | /auth/logout | Thu hồi phiên hiện tại | User |
| users | GET/PATCH | /users/me | Đọc/sửa hồ sơ tài khoản | User |
| families | GET/POST | /families | Gia đình của tôi / tạo gia đình | User |
| families | GET/PATCH | /families/{family_id} | Xem/sửa gia đình | Member / Family Admin |
| families | DELETE | /families/{family_id} | Lưu trữ/xóa mềm gia đình | Family Admin |
| families | GET/POST | /families/{family_id}/branches | Danh sách / tạo nhánh | Member / Family Admin |
| families | PATCH/DELETE | /families/{family_id}/branches/{branch_id} | Sửa/xóa nhánh không còn người tham chiếu | Family Admin |
| families | POST | /families/{family_id}/join-requests | Xin tham gia | User |
| families | GET | /families/{family_id}/join-requests | Danh sách chờ duyệt | Family Admin |
| families | PATCH | /families/{family_id}/join-requests/{user_id} | Duyệt/từ chối | Family Admin |
| genealogy | GET/POST | /families/{family_id}/members | Danh sách / thêm người phả hệ | Member / Family Admin |
| genealogy | GET/PATCH/DELETE | /families/{family_id}/members/{member_id} | Xem/sửa/xóa có kiểm tra quan hệ | Member / Family Admin |
| genealogy | GET/POST | /families/{family_id}/parent-child | Danh sách / tạo quan hệ | Member / Family Admin |
| genealogy | DELETE | /families/{family_id}/parent-child/{parent_id}/{child_id} | Xóa quan hệ | Family Admin |
| genealogy | GET/POST | /families/{family_id}/marriages | Danh sách / thêm hôn nhân | Member / Family Admin |
| genealogy | PATCH/DELETE | /families/{family_id}/marriages/{marriage_id} | Cập nhật/xóa hôn nhân | Family Admin |
| genealogy | GET | /families/{family_id}/genealogy | Đồ thị nodes/edges | Member |
| genealogy | GET | /families/{family_id}/relationships | Quan hệ giữa from_member_id và to_member_id | Member |
| community | GET/POST | /families/{family_id}/posts | Danh sách / đăng bài | Member |
| community | PATCH/DELETE | /families/{family_id}/posts/{post_id} | Sửa/xóa bài | Owner / Family Admin |
| community | GET/POST | /families/{family_id}/posts/{post_id}/comments | Đọc/thêm bình luận | Member |
| community | PATCH/DELETE | /families/{family_id}/comments/{comment_id} | Sửa/xóa bình luận | Owner / Family Admin |
| community | PUT/DELETE | /families/{family_id}/posts/{post_id}/reaction | Đổi/xóa phản ứng của tôi | Member |
| events | GET/POST | /families/{family_id}/events | Danh sách / tạo sự kiện | Member / Family Admin |
| events | GET/PATCH | /families/{family_id}/events/{event_id} | Chi tiết/sửa/hủy bằng status | Member / Family Admin |
| events | PUT | /families/{family_id}/events/{event_id}/rsvp | Cập nhật RSVP của tôi | Member |
| events | GET | /families/{family_id}/events/{event_id}/participants | Danh sách tham gia | Member |
| directory | GET | /families/{family_id}/directory | Lọc tên/nghề/địa điểm/thế hệ theo mốc | Member |
| directory | GET/PATCH | /families/{family_id}/members/{member_id}/profile | Hồ sơ nghề nghiệp/học vấn | Member / linked User hoặc Family Admin |
| heritage | GET/POST | /families/{family_id}/heritage | Danh sách / tạo tư liệu theo type | Member / Family Admin |
| heritage | GET/PATCH/DELETE | /families/{family_id}/heritage/{heritage_id} | Chi tiết/sửa/xóa mềm | Member / Family Admin |
| media | POST | /families/{family_id}/media | Upload multipart; trả media_id | Member |
| media | GET/DELETE | /families/{family_id}/media/{media_id} | Tải có quyền / xóa tệp chưa được liên kết | Member theo quyền đối tượng / Owner hoặc Family Admin |
| media | GET/POST/DELETE | /families/{family_id}/posts/{post_id}/media | Danh sách/gắn/gỡ tệp bài; DELETE dùng media_id | Member / Owner hoặc Family Admin |
| media | GET/POST/DELETE | /families/{family_id}/events/{event_id}/media | Album sự kiện; POST/DELETE dùng media_id | Member / Uploader theo chính sách hoặc Family Admin |
| media | GET/POST/DELETE | /families/{family_id}/heritage/{heritage_id}/media | Tệp tư liệu; POST/DELETE dùng media_id | Member / Family Admin |
| notifications | GET | /notifications | Thông báo của tôi | User |
| notifications | PATCH | /notifications/{notification_id} | Đánh dấu đã đọc | Recipient |
| notifications | POST | /families/{family_id}/announcements | Thông báo cho gia đình | Family Admin |
| dashboard | GET | /families/{family_id}/dashboard | Tổng quan thống kê | Family Admin |
| dashboard | GET | /families/{family_id}/reports | Báo cáo JSON theo type/from/to | Family Admin |
| dashboard | GET | /families/{family_id}/reports/export | CSV cùng bộ lọc | Family Admin |
| ai | POST | /families/{family_id}/ai/search | Tìm kiếm ngữ nghĩa | Member |
| ai | POST | /families/{family_id}/ai/ask | Hỏi đáp có nguồn | Member |
| ai | POST | /families/{family_id}/ai/summarize | Tóm tắt tư liệu có quyền | Member |
| ai | GET | /families/{family_id}/ai/recommendations | Đề xuất tư liệu bằng độ tương đồng; thành viên liên quan | Member |
| admin | GET | /admin/users | Danh sách tài khoản | System Admin |
| admin | PATCH | /admin/users/{user_id} | Khóa/mở tài khoản | System Admin |
| admin | GET | /admin/moderation | Danh sách nội dung cần kiểm duyệt | System Admin |
| admin | POST | /admin/moderation | Ẩn/khôi phục nội dung và ghi lý do | System Admin |
| admin | GET | /admin/audit-logs | Nhật ký phân trang | System Admin |
| admin | GET/PATCH | /admin/settings | Cấu hình cho phép, không chứa secret | System Admin |

## Quy ước
- JSON snake_case, ID số nguyên, thời điểm UTC ISO 8601. Phân trang page/page_size (mặc định 20, tối đa 100) cho danh sách.
- Authorization: Bearer <token>; kiểm tra JWT và USER_SESSIONS chưa bị thu hồi, tài khoản/membership còn hoạt động.
- Member ở bảng là thành viên active của family_id. Owner là chủ đối tượng trong gia đình. Recipient là người nhận, User là tài khoản đã đăng nhập.
- Family Admin chỉ có quyền trong gia đình tương ứng. System Admin được xem công cụ kiểm duyệt, không mặc nhiên hỏi AI tất cả dữ liệu gia đình.
- GET/PATCH: GET theo quyền đọc, PATCH theo quyền ghi nêu sau dấu /. Các thao tác ghi album phải xác định đúng uploader/chủ nội dung.
- Nội dung và tệp gắn với đối tượng ẩn chỉ người có quyền quản trị/kiểm duyệt phù hợp được đọc; tệp chưa gắn chỉ uploader và quản trị gia đình đọc.
- 200/201/204 thành công; 401 chưa xác thực; 403 không đủ quyền; 404 không có tài nguyên; 409 xung đột; 413 vượt dung lượng; 422 sai dữ liệu; 503 dịch vụ AI chưa sẵn sàng.
- POST/DELETE liên kết media dùng JSON {"media_id": 123}; chỉ gỡ liên kết không tự xóa tệp đang được dùng nơi khác.
- Schema chi tiết mỗi endpoint sẽ hoàn thiện trước khi code module, không suy ra payload từ tên file.

## Payload nền tảng
Đăng nhập: {"email":"demo@example.com","password":"..."}; trả access_token, token_type, expires_in và user {id,full_name}. Không trả PasswordHash.
Thêm người: {"full_name":"Nguyễn Văn A","birth_date":"1990-01-15","branch_id":null,"parent_member_ids":[]}.
Duyệt: {"status":"active"} hoặc {"status":"rejected"}.
RSVP PUT: {"status":"going"}; các giá trị going/maybe/declined; gọi lại không tạo dòng trùng.
Quan hệ: GET relationships?from_member_id=1&to_member_id=2; trả path, relation_label, xác định/không xác định. Không đoán vai vế khi thiếu giới tính hoặc quan hệ.
AI search: {"query":"câu hỏi","limit":5}; trả các kết quả gồm heritage_id,chunk_id,text,score.
AI ask: {"question":"..."}; trả answer,sources,mode. Không dùng câu trả lời mô phỏng dưới nhãn AI thật.
AI summarize: {"heritage_id":1}; backend tự lấy nội dung sau kiểm tra quyền.
Lỗi mẫu: {"detail":"Quan hệ tạo chu trình tổ tiên","code":"GENEALOGY_CYCLE"}.

## Điểm thay đổi so với v1
RSVP từ /events/{event_id}/rsvp chuyển sang /families/{family_id}/events/{event_id}/rsvp với PUT. AI chuyển từ /ai/ask sang /families/{family_id}/ai/ask. Frontend và test phải dùng thống nhất hợp đồng v2. API v1 trong tên tiền tố là phiên bản giao thức; v2 của tài liệu là lần cập nhật bộ khung, chưa đổi tiền tố.

Backup/restore là thao tác DBA qua script SQL, không có REST API nhận lệnh hoặc đường dẫn tùy ý.
