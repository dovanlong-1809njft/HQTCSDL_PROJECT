# Kiểm thử giao diện quản trị và đăng nhập — task 7, 8, 9

Hai trang mới là `/admin-config` (admin) và `/member-approval` (admin, family_head). Giao diện dùng layout, Axios, React Hook Form và TanStack Query sẵn có. Tài khoản được xác thực và giới hạn phạm vi chi bởi API task 6.

## Chạy ứng dụng

Backend cần có các đối tượng SQL task 3 và `database/procedures/06_admin_procs.sql` của task 6. Khởi động backend theo [hướng dẫn API](../api/README.md).

Nếu backend đang chạy bằng Docker, các thay đổi trong `apps/backend/app` cần được build vào image mới. Với `.env` hoặc biến môi trường SQL/JWT đã cấu hình, chạy tại thư mục gốc:

```powershell
docker compose up -d --no-deps --build backend
```

Nếu trang báo `Not Found`, kiểm tra `http://localhost:8000/docs` có nhóm admin và `/api/admin/configs` hay chưa. Backend cũ chỉ có nhóm auth cần cập nhật image; nạp SQL riêng sẽ không tạo thêm route HTTP. Sau khi cập nhật backend, tải lại trang web.

Tại `apps/web`, tạo `.env.local` nếu cần:

```env
VITE_API_URL=/api
VITE_PROXY_TARGET=http://localhost:8000
VITE_ENABLE_MOCK_AUTH=false
```

Chạy frontend:

```powershell
npm install --include=dev
npm run dev
```

Đăng nhập bằng tài khoản web có role phù hợp. Admin có thể thêm/sửa/xóa cấu hình và xử lý xác minh; family_head chỉ có trang duyệt thành viên. Cấu hình và yêu cầu chờ được phân trang 20 dòng. Khóa cấu hình giữ nguyên khi sửa; giá trị được phép để trống. Xóa cấu hình cần xác nhận. Sau khi duyệt, danh sách được tải lại để cập nhật cả các yêu cầu cạnh tranh bị tự từ chối.

Các trang có trạng thái tải, lỗi, danh sách rỗng và đang lưu. Lỗi 401 của token hiện tại đưa về đăng nhập; phản hồi 401 từ phiên cũ không xóa phiên mới. Lỗi 403/404/409 khi duyệt làm tải lại danh sách. Thời gian hiển thị theo UTC như API. Khi đăng xuất/đổi tài khoản, trạng thái đăng nhập được đồng bộ giữa các tab và dữ liệu đệm được xóa.

## Chạy kiểm thử tự động

`test_admin_pages.py` dùng pytest và Playwright. Bộ test tự khởi động Vite trên cổng riêng và tự tắt khi xong, không chiếm cổng frontend bạn đang dùng. Các request API đều được giả lập trong trình duyệt; không gọi backend và không ghi SQL Server.

Tại thư mục gốc `HQTCSDL_PROJECT`, cài thư viện kiểm thử:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pip install -r apps/backend/requirements-dev.txt
```

Windows dùng Microsoft Edge có sẵn. Trên Linux/macOS, cài Chromium cho Playwright một lần:

```text
python -m playwright install chromium
```

Chạy test tại thư mục gốc:

```powershell
$env:RUN_TASK7_UI = '1'
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/e2e/test_admin_pages.py -q
```

Bộ test kiểm tra CRUD, giữ dữ liệu form khi lỗi, validation, xác nhận xóa, phân trang, URL trái quyền, hết phiên, duyệt/từ chối và tải lại yêu cầu cạnh tranh, lỗi 409, chống bấm trùng, đăng xuất/xóa storage/đổi tài khoản giữa các tab, phản hồi 401 đến muộn và menu trên màn hình nhỏ. Nếu không đặt `RUN_TASK7_UI=1`, nhóm test được bỏ qua.

Kiểm tra build tại `apps/web`:

```powershell
npm run build
```

Trước khi dùng dữ liệu thật, kiểm tra lại hai trang với backend và database thử đang chạy. Mock API chỉ xác nhận hành vi giao diện và nội dung request; kiểm thử SQL Server thật của task 6 nằm trong [tests/api](../api/README.md).

## Task 8 — dashboard và báo cáo nội dung

Dashboard `/dashboard` gọi API thống kê thật cho admin và family_head, có thẻ số liệu, biểu đồ Recharts và bảng số liệu đầy đủ. Admin xem toàn hệ thống; family_head xem các gia đình có hồ sơ đã liên kết. Member/guest vẫn vào dashboard nhưng không gọi API thống kê quản trị. Trang dashboard được tải riêng để thư viện biểu đồ không nằm trong gói đăng nhập ban đầu.

Trang `/reports` và menu **Báo cáo nội dung** chỉ dành cho admin. Có lọc pending/resolved/dismissed và phân trang 20 dòng. **Bỏ qua báo cáo** giữ nguyên nội dung. **Gỡ nội dung** cần xác nhận xóa vĩnh viễn; sau xử lý, danh sách được tải lại để cập nhật các báo cáo liên quan, đồng thời làm mới cache thống kê. Nội dung không còn hoặc không hỗ trợ gỡ chỉ có thể bỏ qua báo cáo.

Nạp SQL task 8 theo [hướng dẫn API](../api/README.md#task-8--thống-kê-và-kiểm-duyệt-nội-dung), rồi cập nhật backend. Với Docker, build lại dịch vụ cần dùng tại thư mục gốc, khi biến môi trường SQL/JWT đã cấu hình:

```powershell
docker compose up -d --no-deps --build backend frontend
```

Không chạy lại script khởi tạo/seed trên database đang có dữ liệu để cập nhật riêng task 8.

Bộ test `test_admin_pages.py` dùng cùng lệnh và cờ `RUN_TASK7_UI=1` ở trên cho cả task 7 và 8. Phần task 8 kiểm tra số liệu/biểu đồ, phạm vi family_head, chặn member/guest, lỗi và tải lại, danh sách rỗng, xác nhận xóa, giữ nguyên nội dung khi bỏ qua, lỗi 409, đóng báo cáo liên quan, cập nhật thống kê, phân trang khi có đúng 20 hoặc 21 dòng, chặn bấm trùng, hiển thị văn bản HTML an toàn và bố cục mobile. Luồng đăng nhập thật của task 9 nằm trong nhóm riêng bên dưới.

## Task 9 — luồng đăng nhập xuyên suốt

`test_login_flow.py` chạy **Edge/Chromium → Vite proxy → FastAPI/Uvicorn → SQL Server thật**. Test nhập form đăng nhập/đăng ký, nhận JWT thật và xác nhận tài khoản qua `/api/auth/me`. Không điền sẵn token hoặc người dùng vào localStorage, không giả lập response đăng nhập. Riêng ca mất mạng chủ động hủy request để kiểm tra không đăng nhập bằng tài khoản demo khi backend không kết nối được.

`conftest.py` dùng chung trình duyệt và cách khởi động Vite cho hai nhóm test. Mỗi nhóm có Vite trên cổng riêng; task 9 còn tự chạy FastAPI trên cổng riêng rồi tự tắt khi xong. Các biến `VITE_API_URL=/api`, `VITE_PROXY_TARGET` trỏ vào backend thử và `VITE_ENABLE_MOCK_AUTH=false` chỉ áp dụng trong process test. Không dùng backend Docker đang chạy, không sửa `.env` của dự án.

Test dùng lại fixture tạo database từ task 6, tên `FamilyConnect_Task6Test_<uuid>`, và tự xóa khi kết thúc. Mỗi ca nạp lại `tests/database/task6.integration.sql` và `tests/database/task9.integration.sql`; mật khẩu được băm bằng chính hàm Argon2 của ứng dụng. Các file T-SQL fixture có chặn chạy ngoài database thử. Không chạy chúng bằng tay trên FamilyConnect đang dùng.

Tài khoản Windows chạy test cần quyền tạo/xóa database và `EXECUTE AS USER` trên SQL Server local, giống kiểm thử API. Cài frontend dependencies trong `apps/web` và `apps/backend/requirements-dev.txt` trước; không cần khởi động Docker, backend hoặc Vite bằng tay.

Chạy riêng task 9 tại thư mục gốc:

```powershell
$env:RUN_TASK9_E2E = '1'
$env:TASK6_SQL_SERVER = 'localhost'

# Duong dan ngan giup mssql-python nap binary khi thu muc du an co tieng Viet.
$task9Packages = & .\.venv\Scripts\python.exe -X utf8 -c "import ctypes,sysconfig; b=ctypes.create_unicode_buffer(32768); ctypes.windll.kernel32.GetShortPathNameW(sysconfig.get_paths()['purelib'],b,len(b)); print(b.value)"
$env:PYTHONPATH = $task9Packages

.\.venv\Scripts\python.exe -X utf8 -m pytest tests/e2e/test_login_flow.py -q
```

Chạy chung task 7–9 trong cùng phiên PowerShell:

```powershell
$env:RUN_TASK7_UI = '1'
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/e2e -q
```

Không đặt `RUN_TASK9_E2E=1` thì bỏ qua module đăng nhập thật; không đặt `TASK6_SQL_SERVER` thì bỏ qua phần cần SQL Server. Nhóm UI giả lập task 7–8 vẫn chạy riêng với `RUN_TASK7_UI=1` và không cần SQL Server.

| Ca | Nội dung | Kết quả cần đạt |
| --- | --- | --- |
| TC01–04 | Đăng nhập admin, family_head, member, guest từ URL cần đăng nhập | Nhận JWT thật; trở về trang được phép; vai trò thấp không gọi API quản trị |
| TC05–07 | Sai mật khẩu, email không tồn tại, tài khoản khóa | API 401; ở lại form; không lưu token |
| TC08 | Email sai định dạng, mật khẩu quá ngắn | Báo validation; không gửi request đăng nhập |
| TC09 | Đăng ký tên Unicode → đăng xuất → đăng nhập lại | Tài khoản lưu trong SQL với mật khẩu băm; role member; cùng UserId |
| TC10 | Đăng ký email đã tồn tại | API 409; hiển thị lỗi; không đăng nhập |
| TC11 | Xác nhận mật khẩu không khớp | Chặn request đăng ký |
| TC12 | Reload, mở tab khác, đăng xuất và đổi tài khoản | Giữ phiên khi reload; đồng bộ đăng xuất/đăng nhập; không giữ dữ liệu admin |
| TC13 | JWT hết hạn | Backend thử phát JWT đã hết hạn; API bảo vệ trả 401; xóa phiên |
| TC14 | Khóa tài khoản sau khi đăng nhập | Request tiếp theo trả 401 và về đăng nhập |
| TC15 | Đổi admin thành member khi JWT còn hạn | Backend đọc quyền hiện tại trong SQL; trả 403, ẩn dữ liệu cấu hình |
| TC16 | Mất kết nối khi đăng nhập | Hiển thị lỗi; không chuyển sang tài khoản demo |

TC13 chỉ thay thời hạn JWT trong process backend thử của ca đó. Tài khoản của fixture (chỉ có trong database thử): `admin@example.com`, `head@example.com`, `member@example.com`, `guest@example.com`, `inactive@example.com`, cùng mật khẩu `Task9-Test-Password!2026`. Tài khoản cuối bị khóa. Không dùng các thông tin này làm tài khoản thật của dự án.
