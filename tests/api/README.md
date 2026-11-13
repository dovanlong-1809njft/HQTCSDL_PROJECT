# Kiểm thử API quản trị — task 6

`test_admin.py` gọi FastAPI thật và SQL Server thật. Bộ test tự tạo database có tên `FamilyConnect_Task6Test_<uuid>`, nạp các file SQL hiện tại, chạy bằng database user chỉ có quyền đọc/gọi Procedure và tự xóa database thử khi kết thúc. Dữ liệu thử và Trigger mô phỏng lỗi audit viết bằng T-SQL trong [task6.integration.sql](../database/task6.integration.sql).

Tài khoản Windows chạy test cần quyền tạo/xóa database và `EXECUTE AS USER` trên SQL Server thử. Mỗi ca test nạp lại dữ liệu mẫu trong database thử; không dùng dữ liệu FamilyConnect đang làm.

Tại thư mục `HQTCSDL_PROJECT`, cài môi trường và chạy:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -X utf8 -m pip install -r apps/backend/requirements-dev.txt
$env:TASK6_SQL_SERVER = 'localhost'
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/api/test_admin.py -q
```

`TASK6_SQL_SERVER` dùng cùng tên server như SSMS, ví dụ `localhost` hoặc `.\SQLEXPRESS`. Chỉ đặt `TASK6_SQL_PORT` nếu muốn chỉ định cổng TCP. Nếu chưa đặt `TASK6_SQL_SERVER`, pytest bỏ qua nhóm kiểm thử cần SQL Server.

Trên máy Windows có đường dẫn dự án chứa tiếng Việt, driver `mssql-python` hiện tại có thể báo thiếu binary dù các file đã được cài. Có thể tạo virtualenv tại đường dẫn không dấu, hoặc dùng đường dẫn ngắn của thư mục package trong phiên PowerShell đang chạy test:

```powershell
$task6Packages = & .\.venv\Scripts\python.exe -X utf8 -c "import ctypes,sysconfig; b=ctypes.create_unicode_buffer(32768); ctypes.windll.kernel32.GetShortPathNameW(sysconfig.get_paths()['purelib'],b,len(b)); print(b.value)"
$env:PYTHONPATH = $task6Packages
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/api/test_admin.py -q
```

Bộ test kiểm tra JWT thiếu/sai/hết hạn, tài khoản khóa, RBAC, CRUD cấu hình, dữ liệu Unicode, khóa trùng, phân trang, phạm vi chi/gia đình, chặn tự duyệt, liên kết thành viên, tự từ chối yêu cầu cạnh tranh, commit, audit và rollback khi ghi audit thất bại. Các lỗi SQL được kiểm tra qua HTTP response và trạng thái dữ liệu sau request.

## Áp dụng task 6 vào database đang dùng

Sau khi đã nạp schema và các đối tượng task 3, mở `database/procedures/06_admin_procs.sql` trong SSMS. Bật **Query → SQLCMD Mode**, thêm dòng sau ở đầu truy vấn rồi Execute:

```sql
:setvar DB_NAME "FamilyConnect"
```

Backend tự đăng ký router admin trong `apps/backend/app/api/router.py`. Khởi động từ `apps/backend` bằng `python -m uvicorn app.main:app --reload`, mở `http://127.0.0.1:8000/docs` và đăng nhập bằng tài khoản có role phù hợp. Kết nối database của ứng dụng dùng cấu hình `.env` hiện có; `app_backend` đã có quyền EXECUTE trên schema core nên gọi được các Procedure mới.

## Task 8 — thống kê và kiểm duyệt nội dung

| API | Quyền | Hành vi |
| --- | --- | --- |
| `GET /api/admin/statistics` | admin, family_head | Số thành viên, bài viết, sự kiện theo gia đình. Admin xem tất cả; family_head chỉ xem gia đình có hồ sơ liên kết bằng `genealogy.Members.UserId`. Chưa có liên kết thì trả danh sách rỗng. |
| `GET /api/admin/reports?status=pending&limit=20&offset=0` | admin | Danh sách báo cáo, người gửi, lý do, nội dung và khả năng gỡ. `status`: pending/resolved/dismissed; limit 1–200; offset không âm. |
| `PATCH /api/admin/reports/{report_id}/resolve` | admin | Body chỉ gồm `decision`: resolved hoặc dismissed. Người xử lý luôn lấy từ JWT và tài khoản hiện tại. |

`dismissed` chỉ đóng báo cáo được chọn, giữ nguyên nội dung. `resolved` gọi `community.usp_ResolveReportedContent` của task 3: xóa nội dung thật, đóng các báo cáo pending liên quan và ghi audit trong cùng giao tác. Gỡ bài viết sẽ xóa cả bình luận, ảnh và phản ứng. Nếu bảng `heritage.KnowledgeChunks` đã tồn tại, chỉ các đoạn kiến thức có `SourceType = 'post'` và `SourceId` trùng bài viết bị gỡ mới được xóa; chưa có bảng AI vẫn gỡ bài bình thường. Photo chỉ hỗ trợ ảnh trong `community.PostMedia`. Báo cáo đã xử lý trả 409; báo cáo/nội dung không còn hoặc loại ảnh không hỗ trợ trả 404. Khi ghi audit lỗi, toàn bộ thay đổi, kể cả dữ liệu AI, được rollback.

Khi cập nhật database hiện có, bật SQLCMD Mode trong SSMS và chạy lần lượt:

```sql
:setvar DB_NAME "FamilyConnect"
:r database/views/03_community_views.sql
:r database/triggers/03_community_triggers.sql
:r database/procedures/01_core_procs.sql
:r database/procedures/07_dashboard_reports_procs.sql
```

Các đường dẫn `:r` tính từ thư mục gốc dự án; có thể mở từng file trong SSMS và đặt biến `DB_NAME` thay thế. Cần chạy lại `01_core_procs.sql` để cập nhật kiểm tra bảng AI trong thủ tục xử lý báo cáo. Task 8 không yêu cầu nạp schema AI. Hai file community ở trên sửa lỗi cú pháp chú thích và biểu thức tổng hợp của trigger khi khởi tạo database mới; không nạp lại seed.

Kiểm thử API/SQL trên database thử riêng, dùng lại fixture và cấu hình `TASK6_SQL_SERVER` ở trên:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/api/test_admin.py tests/api/test_reports.py tests/api/test_config.py -q
```

`test_reports.py` nạp dữ liệu T-SQL từ `tests/database/task8.integration.sql`, kiểm tra phân quyền, phạm vi gia đình, số đếm, nội dung không còn, phân trang, gỡ từng loại nội dung, đóng báo cáo liên quan, audit và rollback. Các ca AI kiểm tra cả khi chưa có bảng (kể cả triển khai thủ tục trước AI), khi đã có dữ liệu, giữ nguyên kiến thức của nguồn khác và khôi phục đầy đủ khi audit lỗi. Fixture chỉ chạy trong database tên `FamilyConnect_Task6Test_<uuid>`; không ghi vào FamilyConnect đang dùng.
