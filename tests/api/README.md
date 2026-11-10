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
