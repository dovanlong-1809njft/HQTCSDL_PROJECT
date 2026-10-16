# Bản đồ tài liệu FamilyConnect — cập nhật 16/10/2026

Tài liệu được chia theo mục đích để thành viên mới **đọc từ hiện trạng tới kế hoạch**, tránh nhầm giữa đã code và dự kiến.

## A. Đọc đầu tiên (10–20 phút)

1. [`../README.md`](../README.md): giới thiệu dự án và cách chạy bản Frontend.
2. [`PROJECT_STATUS.md`](PROJECT_STATUS.md): những gì đã có, chưa có và điểm cần sửa.
3. [`FRONTEND_FEATURE_MATRIX.md`](FRONTEND_FEATURE_MATRIX.md): từng trang HTML, module JS, trạng thái demo.
4. [`DEVELOPMENT_HISTORY.md`](DEVELOPMENT_HISTORY.md): trình tự xây dựng, ngày có/chưa có chứng cứ.
5. [`structure-inventory.md`](structure-inventory.md): kiểm kê toàn bộ file thực tế.

## B. Phân chia công việc / làm việc nhóm

- [`team-guide.md`](team-guide.md): cách đọc tài liệu, quy trình Git, nguyên tắc cập nhật khi thay đổi code.
- [`file-ownership.md`](file-ownership.md): đầu mối đề xuất A–E cho từng file, **chưa phải người được phân công**.
- [`task-checklist.txt`](task-checklist.txt): checklist phân biệt có mã mẫu và đã nghiệm thu.
- [`implementation-order.md`](implementation-order.md): lịch 21 ngày gốc, cần hiệu chỉnh theo thời gian còn lại.
- [`decision-log.md`](decision-log.md): các quyết định công nghệ và UX đã chốt / còn cần đối chiếu.

## C. Tài liệu thiết kế mục tiêu — KHÔNG phải API/DB đã chạy

- `requirements.md`, `use-cases.md`: yêu cầu chức năng và ca sử dụng.
- `architecture.md`, `database-design.md`, `api-documentation.md`: kiến trúc, mô hình bảng và hợp đồng API **dự kiến**.
- `ai-design.md`, `dependencies.md`: mục tiêu tích hợp AI và thư viện.
- `backup-restore.md`, `deployment-guide.md`: hướng dẫn triển khai mục tiêu và phần hiện chạy được.
- `diagrams/`: mã sơ đồ Mermaid.

## D. Nhật ký Frontend theo module

| Module / đợt cải tiến | Tài liệu |
|---|---|
| Tổng quan / khởi đầu | `FRONTEND_STEP1.md` |
| Gia đình | `FRONTEND_GIADINH.md` |
| Gia phả | `FRONTEND_CAYGIAPHA.md` |
| Danh bạ | `FRONTEND_DANHBA.md` |
| Cộng đồng | `FRONTEND_CONGDONG.md` |
| Sự kiện | `FRONTEND_SUKIEN.md` |
| Di sản | `FRONTEND_DISAN.md` |
| Trợ lý AI mẫu | `FRONTEND_TROLYAI.md` |
| Báo cáo | `FRONTEND_BAOCAO.md` |
| Thông báo | `FRONTEND_THONGBAO.md` |
| Hồ sơ | `FRONTEND_HOSO.md` |
| Quản trị | `FRONTEND_QUANTRI.md` |
| Sidebar hover | `FRONTEND_SIDEBAR.md` |
| Sửa giao diện V3 | `FRONTEND_UI_FIXES_V3.md` |
| Đăng nhập/menu tài khoản V4 | `FRONTEND_DANGNHAP_TAIKHOAN.md` |
| Sửa chế độ tối V5 | `FRONTEND_DARK_MODE_V5.md` |

## E. Kiểm thử và quản lý tài liệu

- `VALIDATION.md`: lịch sử các kiểm tra từng bước; không tự áp dụng kết quả cũ cho bản mới.
- `test-report.md`: kế hoạch kiểm thử; cần kết quả thực tế trước khi đánh dấu Pass.
- `DOCUMENT_AUDIT.md`: báo cáo các sai lệch phát hiện trong ZIP.
- `DOCUMENT_REVIEW_CANDIDATES.md`: đề xuất file có thể xem xét xóa/chuyển sau này; **chưa xóa gì**.
- `CHANGELOG_STRUCTURE.md`: lịch sử thay đổi cấu trúc v2, giữ nguyên vì có giá trị truy vết.
- `terms-quick-reference.txt`, `file-guide.md`: giải thích thuật ngữ Anh–Việt, đuôi file.

**Quy tắc:** Mỗi khi thay đổi code, cập nhật ít nhất tài liệu module, `PROJECT_STATUS.md`, checklist và nhật ký nếu đó là mốc tính năng/phiên bản mới.
