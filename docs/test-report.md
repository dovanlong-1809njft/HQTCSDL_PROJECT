# Kế hoạch và kết quả kiểm thử

Bộ khung v2 CHƯA chạy kiểm thử chức năng/SQL/thiết bị/Docker/AI. Kiểm tra cấu trúc và cú pháp là kiểm tra riêng, không ghi Pass cho tính năng.

| Nhóm | Tình huống bắt buộc | Bằng chứng |
|---|---|---|
| Auth | Sai mật khẩu, khóa tài khoản, token hết hạn/thu hồi | HTTP và log đã che thông tin |
| Quyền | Thay ID sang gia đình khác; membership pending/suspended | API 403/404, dữ liệu không rò |
| Gia phả | Chu trình, tự liên kết, khác gia đình, hai phiên quan hệ ngược | SQL trước/sau và API |
| Giao tác | Thêm người xong gặp lỗi liên kết | Không có bản ghi dở dang |
| Đồng thời | Hai phiên duyệt/tranh chỗ cuối | Ghi @@SPID, thứ tự bước, isolation, kết quả |
| Cộng đồng/tệp | CRUD, phản ứng, upload sai loại/quá lớn/tải không quyền | API và giao diện |
| Sự kiện | RSVP lặp, sửa/hủy, album, nhắc không trùng | SQL + API + worker |
| Danh bạ/di sản | Lọc nghề/địa điểm/thế hệ; các loại tư liệu | Bộ dữ liệu có đáp án |
| AI | Đồng nghĩa tiếng Việt, nguồn thiếu/bị xóa, quyền, timeout | Câu hỏi, nguồn, phản hồi, model |
| Báo cáo | Dashboard/CSV khớp SQL, ô công thức | File xuất và truy vấn đối chiếu |
| Vận hành | Docker trên máy thứ hai, upload tồn tại sau restart | Lệnh build/run và kết quả |
| Phục hồi | SQL + volume tệp, restore DB riêng | Thời gian và dữ liệu so sánh |
| Thiết bị | Android/iOS/Windows; web/PWA | Thiết bị/trình duyệt/ảnh thực tế |

Mỗi kết quả cần: mã FR/NF, commit, ngày, người chạy, môi trường, đầu vào, mong đợi, thực tế, Pass/Fail/Blocked, bằng chứng. tests/*.py và database/tests/*.sql hiện chỉ là khung.
