# Nhật ký hình thành FamilyConnect (Development History)

## Dòng thời gian đáng tin cậy theo những gì đang có

| Ngày / giai đoạn | Độ tin cậy về ngày | Thay đổi | Mã và tài liệu tương ứng |
|---|---|---|---|
| **14/10/2026** | **Ghi trực tiếp trong tài liệu** | Chuẩn hóa cấu trúc v2; mở rộng thiết kế CSDL/API, tổ chức thư mục; chuẩn bị Dashboard mẫu | `docs/CHANGELOG_STRUCTURE.md`, `docs/FRONTEND_STEP1.md`, `frontend/pages/dashboard.html` |
| **15/10/2026** | **Ghi trực tiếp trong tài liệu** | Triển khai trang “Gia đình của tôi” trên Frontend mẫu | `docs/FRONTEND_GIADINH.md`, `frontend/pages/family.html` |
| **Sau bước Gia đình — ngày từng bước chưa xác thực** | **Thứ tự do tài liệu ghi, không đủ bằng chứng cho ngày** | Gia phả (bước 3), Danh bạ (4), Cộng đồng (5), Sự kiện (6), Di sản (7), AI mô phỏng (8), Báo cáo (9), Thông báo (10), Hồ sơ/Quản trị | `docs/FRONTEND_CAYGIAPHA.md` ... `docs/FRONTEND_QUANTRI.md` và các module tương ứng |
| **16/10/2026 — Sidebar** | **Theo tiến trình trao đổi, chưa có commit xác minh** | Chuyển Sidebar sang icon rail 3.05rem → 15rem bằng CSS/JS; có ghim, xử lý mobile | `docs/FRONTEND_SIDEBAR.md`, `sidebar.css`, `sidebar.js` |
| **16/10/2026 — V3** | **Theo tiến trình trao đổi; tên phiên bản xác nhận bằng tài liệu** | Căn sơ đồ gia phả, đồng bộ avatar, bỏ trùng Sidebar, thông báo nổi, đổi vị trí nút ghim | `docs/FRONTEND_UI_FIXES_V3.md`, `notification-popover.js`, `profile-badge.js` |
| **16/10/2026 — V4** | **Theo tiến trình trao đổi; tên phiên bản xác nhận bằng tài liệu** | Thêm Đăng nhập/Đăng ký, giao diện Google/Facebook chờ OAuth, menu avatar, Sáng/Tối và đăng xuất demo | `docs/FRONTEND_DANGNHAP_TAIKHOAN.md`, `auth.js`, `account-menu.js`, `auth-page.js` |
| **16/10/2026 — V5** | **Theo tiến trình trao đổi; tên phiên bản xác nhận bằng tài liệu** | Sửa quy tắc tương phản ở chế độ tối, nhãn biểu đồ báo cáo | `docs/FRONTEND_DARK_MODE_V5.md`, `theme.css`, `reports.js` |
| **16/10/2026 — rà soát tài liệu hiện tại** | **Ngày cập nhật tài liệu này** | Đồng bộ README, kiểm kê file, checklist, hướng dẫn nhóm, trạng thái và điểm chưa nhất quán; **không sửa code** | `docs/DOCUMENT_AUDIT.md` và `docs/structure-inventory.md` |

## Cách đọc “bước” và “phiên bản”

- “Bước 1–10” trong `FRONTEND_*.md` là **thứ tự phát triển chức năng**, không nhất thiết tương đương 10 ngày hoặc 10 commit.
- “V3, V4, V5” là các **đợt cải tiến Frontend** được đặt tên trong quá trình trao đổi, **không phải Git tags đã xác minh**.
- Một ngày được nhắc trong tài liệu không tự chứng minh ngày code được push lên `main`. Chỉ `git log`, Pull Request, issue hoặc commit có liên quan mới xác minh được.
- Các ảnh giao diện từng được thiết kế là tài liệu tham khảo; mã nguồn hiện tại mới là bằng chứng có triển khai.

## Khi bắt đầu dùng GitHub làm lịch sử chính thức

Chạy trên PowerShell tại repo đã clone:

```powershell
git log --date=iso --pretty=format:"%h | %ad | %an | %s" --all
git log --follow -- frontend/pages/community.html
git log --follow -- frontend/assets/css/theme.css
```

Người phụ trách đối chiếu commit/PR với các mốc trên, bổ sung **cột commit link** nếu có. Không đoán ngày từ thời gian chỉnh sửa ZIP vì nén/giải nén/sao chép có thể thay đổi timestamp.

## Mẫu ghi thêm một bản cập nhật

```text
Ngày: YYYY-MM-DD (đã đối chiếu commit / chỉ ghi nhận từ trao đổi)
Phiên bản hoặc nhánh: ...
Chức năng: ...
File sửa: ...
Thay đổi chính: ...
Cách kiểm tra: ...
Kết quả: Chưa thử / Đạt / Lỗi còn tồn tại
Commit hoặc PR: ...
Tài liệu cần cập nhật: ...
```

## Những điểm chưa xác minh trong lịch sử

- Ngày chính xác từng trang từ Gia phả đến Quản trị được triển khai vào máy hoặc GitHub.
- Trạng thái “PASS trình duyệt” ở máy cá nhân cho từng bước.
- Thời điểm và nhánh mà mỗi file đã được merge.
- Thời điểm **commit hoặc merge** sửa `frontend/index.html` vào GitHub chưa xác minh; mã nguồn được chỉnh trong gói V7 ngày 16/10/2026 theo yêu cầu trao đổi.

## 16/10/2026 — Cập nhật V7: Lối vào ứng dụng

- **Nguồn ngày:** lượt yêu cầu hiện tại và bản ZIP được tạo cùng ngày; **không xác thực được ngày commit hoặc người commit** vì chưa có `.git`.
- **Lý do:** Trong bản V6, `frontend/index.html` vẫn có meta refresh về `pages/dashboard.html`, mâu thuẫn với luồng Đăng nhập V4.
- **Mã đã chỉnh:** `frontend/index.html` bỏ meta refresh; nạp `assets/js/core/auth.js` để kiểm tra phiên dùng thử hiện tại.
- **Luồng mới:** chưa đăng nhập → `pages/login.html`; đã có phiên mẫu → `pages/dashboard.html`; dùng `location.replace()` để không tạo lịch sử chuyển hướng thừa.
- **Phạm vi:** không sửa auth.js, không sửa logic Backend/Database; cập nhật các tài liệu đang ghi lỗi cũ.
- **Kiểm thử:** kiểm tra tự động hai hướng điều hướng và cấu trúc ZIP; người phụ trách cần mở thử trên trình duyệt thật trước khi đánh dấu nghiệm thu.
