# Kiểm thử giao diện quản trị — task 7

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
