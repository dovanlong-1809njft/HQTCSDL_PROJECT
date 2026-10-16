# Hướng dẫn làm việc nhóm FamilyConnect (Team Guide)

> Dành cho thành viên lần đầu tham gia dự án. **Đây là hướng dẫn phân công theo trách nhiệm, không khẳng định nhóm đã có đủ người hoặc đã giao việc chính thức.**

## 1. Đọc và chạy thử trước khi nhận task

1. Xem `README.md` ở gốc để biết công nghệ, cách chạy.
2. Đọc `docs/PROJECT_STATUS.md` để phân biệt phần có mã Frontend, phần mô phỏng và phần Backend/SQL chưa làm.
3. Đọc `docs/DEVELOPMENT_HISTORY.md` để hiểu tiến trình phát triển; không coi ngày tài liệu là ngày commit khi chưa đối chiếu Git.
4. Xem `docs/structure-inventory.md` và `docs/FRONTEND_FEATURE_MATRIX.md` để tìm đúng file.
5. Chạy Frontend ở localhost, thử Đăng nhập mẫu, trang Gia đình, Gia phả, Cộng đồng, Thông báo nổi, nút ghim và Sáng/Tối.
6. Chọn task trong `docs/task-checklist.txt`; ghi rõ người nhận, nhánh và điều kiện hoàn thành trên GitHub Issue/Project.

## 2. Năm nhóm trách nhiệm đề xuất A–E

| Nhóm | Vai trò | File/đầu mối chính |
|---|---|---|
| A — Database | Thiết kế bảng/SQL Server/T-SQL, ACID, concurrent access, backup | `database/**`, `docs/database-design.md` |
| B — Backend Core | FastAPI, Auth, API nền, phân quyền, giao dịch tài khoản/gia đình | `backend/app/core`, `db`, `routers/auth.py`, `families.py` |
| C — Genealogy | Gia phả, quan hệ và danh bạ cả Frontend/Backend | `genealogy*`, `directory*` |
| D — Frontend & Community | Thành phần UI chung, sidebar, đăng nhập mẫu, cộng đồng, sự kiện, upload | `frontend/assets/css/*`, `core/*`, `community*`, `events*` |
| E — AI, Reporting & Integration | AI, di sản, thống kê, thông báo, tài liệu/QA | `ai*`, `heritage*`, `reports*`, `notifications*`, `docs/*` |

**Thực tế hiện tại:** người phát triển đang tự dựng mẫu để các thành viên khác nhìn tổng thể. Chỉ gán người sau khi cả nhóm xác nhận. Bảng `file-ownership.md` là **đầu mối đề xuất**, không phải quyền sở hữu độc quyền.

## 3. Trình tự kỹ thuật nên tiếp tục

1. **Đóng mốc Frontend mẫu:** kiểm tra giao diện và ghi lỗi; không thêm tính năng chỉ vì thấy còn chỗ trống.
2. **Chốt mô hình dữ liệu:** ERD, khóa chính/ngoại, ràng buộc, phân quyền; đối chiếu mọi form và mô tả trang hiện có.
3. **Xây dựng SQL Server:** tạo bảng/dữ liệu mẫu, giao tác, Stored Procedure, View/Function phù hợp đề tài.
4. **Viết FastAPI:** kết nối, Auth thật, API theo hợp đồng rồi thay dữ liệu mẫu ở UI bằng kết quả API.
5. **Kiểm thử tích hợp và báo cáo:** giao tác/đồng thời, tính đúng đắn, bảo mật, minh chứng chạy và tài liệu.

Lịch 21 ngày ban đầu có ở `implementation-order.md`; **đó là kế hoạch gốc cần điều chỉnh theo thời gian còn lại**, không có nghĩa nhóm phải làm lại Frontend từ đầu.

## 4. GitHub: quy trình hằng ngày

- Tạo branch ngắn `feature/<chuc-nang>` hoặc `docs/<chu-de>` từ `main` mới nhất.
- Đầu ngày: `git pull --ff-only origin main` trên nhánh main; sau đó tạo/chuyển branch công việc.
- Commit nhỏ với nội dung rõ: `docs: sync frontend project status`, `feat: ...`, `fix: ...`.
- Mở Pull Request (yêu cầu hợp nhất) ghi những file sửa, cách thử, hình/ảnh minh chứng và task liên quan.
- Tránh hai người cùng sửa một file HTML/CSS dùng chung; thống nhất người duyệt và trao đổi trước.
- **Không commit `.env`, khóa API, mật khẩu thật, file `.bak`, `.mdf`, `.ldf` hoặc dữ liệu cá nhân thật**.

## 5. Mỗi thay đổi code phải cập nhật tài liệu nào?

| Trường hợp | File cần cập nhật |
|---|---|
| Thêm/sửa một trang Frontend | `FRONTEND_<MODULE>.md`, `FRONTEND_FEATURE_MATRIX.md`, `PROJECT_STATUS.md` |
| Thêm/xóa/đổi tên đường dẫn file | `structure-inventory.md`, `file-ownership.md`, các README trỏ tới nó |
| Thêm API hoặc đổi JSON | `api-documentation.md`, `requirements.md` nếu yêu cầu đổi |
| Đổi bảng/cột/quan hệ | `database-design.md`, các script SQL, tài liệu API liên quan |
| Sửa UI/UX ảnh hưởng nhiều trang | `DEVELOPMENT_HISTORY.md`, tài liệu cập nhật Vx, checklist kiểm thử |
| Có bug chưa sửa | GitHub Issue + `task-checklist.txt`, không đánh dấu PASS |
| Chuẩn bị demo/nộp | `test-report.md`, `user-guide.md`, `deployment-guide.md` |

## 6. Tiêu chuẩn nhận việc xong

Không chỉ tạo file. Chức năng hoàn thành khi có mã chạy được, test theo điều kiện nghiệm thu, README/docs mô tả đúng, người khác có thể chạy lại và đã được review. **Frontend mock** được ghi rõ là mock, không tự gọi là “API xong” hoặc “Database xong”.

## 7. Bảo toàn file tài liệu

Không tự xóa tài liệu cũ để tránh nhầm: lịch sử vẫn có giá trị. File đáng cân nhắc chỉ được liệt kê trong `DOCUMENT_REVIEW_CANDIDATES.md`; chủ dự án xem và duyệt trước khi có commit xóa. Khi đổi cấu trúc lớn, chụp kiểm kê trước và sau để đối chiếu.
