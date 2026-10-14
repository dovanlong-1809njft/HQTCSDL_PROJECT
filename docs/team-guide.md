# Làm việc nhóm

## Nhóm trách nhiệm
- A — CSDL: thiết kế, T-SQL, quyền SQL, transaction/concurrency, backup/restore.
- B — Nền tảng và tài khoản: cấu hình/kết nối, auth, users, families/branches/membership, admin.
- C — Gia phả/danh bạ: người, cha-con, hôn nhân, cây, truy vấn quan hệ, hồ sơ nghề nghiệp.
- D — Giao diện chung/cộng đồng/sự kiện/tệp: UI chung, account UI, posts, events, media, PWA.
- E — Di sản/AI/báo cáo/tích hợp: heritage, notifications, AI, dashboard/reports, Docker và QA chung.

Đây là 5 nhóm trách nhiệm, không giả định số người. E có tải lớn, nên A hỗ trợ báo cáo/nhắc lịch SQL và D hỗ trợ giao diện di sản. Một file có một đầu mối trong file-ownership.md nhưng nhiều người có thể hỗ trợ qua review.

Lịch duy nhất: implementation-order.md. Không duy trì lịch ngày thứ hai ở đây.
Mỗi tính năng làm trên nhánh ngắn feature/<ten-tinh-nang>, commit nhỏ, mở Pull Request và review trước khi merge. main giữ bản chạy ổn; tích hợp hằng ngày.
Đổi bảng/cột: A cập nhật database-design và báo người viết repository. Đổi payload: B điều phối api-documentation và frontend/test cùng cập nhật.
Không commit .env/API key/backup/dữ liệu thật. Kết quả test phải gắn commit/môi trường; không ghi Pass cho test còn TODO.
