# FamilyConnect

FamilyConnect là đề tài môn **Hệ quản trị cơ sở dữ liệu**, hướng tới xây dựng nền tảng cộng đồng gia đình số để quản lý gia phả, kết nối thành viên, tổ chức sự kiện và lưu giữ di sản gia đình. Trọng tâm của dự án là thiết kế và khai thác cơ sở dữ liệu SQL Server; ứng dụng web dùng để minh họa các luồng nghiệp vụ.

## Trạng thái dự án

- Frontend có giao diện đăng nhập, đăng ký và trang tổng quan cơ bản.
- Backend có health check và API đăng ký, đăng nhập, xem tài khoản hiện tại.
- ERD là thiết kế dự kiến gồm 14 bảng thuộc 5 schema. Xem [sơ đồ ERD](docs/erd/README.md).
- Các file SQL trong `database/schema/` và `database/seed/` đang để trống để nhóm bổ sung. Vì vậy database chưa được khởi tạo và các API cần đọc/ghi dữ liệu chưa hoạt động đầy đủ.
- Các thư mục kiểm thử API, database và hiệu năng chưa có test thực thi. Xem [kế hoạch kiểm thử](tests/README.md).

## Công nghệ

- Frontend: React, Vite, JavaScript, Tailwind CSS, React Router, Axios, TanStack Query, React Hook Form.
- Backend: FastAPI, SQLAlchemy, JWT.
- Database: Microsoft SQL Server 2025 và T-SQL.
- Đóng gói môi trường phát triển: Docker Compose.
- React Flow và Recharts hiện có trong dependencies, dành cho phần cây gia phả và biểu đồ khi các chức năng đó được triển khai.

## Cấu trúc dự án

```text
backend/                 # API FastAPI và các module nghiệp vụ
frontend/                # Ứng dụng web React viết bằng JavaScript
database/
  schema/                # Các script tạo schema và bảng; hiện đang trống
  seed/                  # Script dữ liệu mẫu; hiện đang trống
  shared/                # Script chỉ chạy trên DB chung (phân quyền theo schema)
  init.sh                # Chạy các file SQL theo thứ tự tên
docs/
  requirements/          # Yêu cầu, vai trò và use case
  architecture/          # Kiến trúc hệ thống
  erd/                   # ERD thiết kế
  api-spec/              # Đặc tả API
tests/                   # Kế hoạch và vị trí dành cho kiểm thử
docker-compose.yml       # Khai báo SQL Server, backend và frontend
```

Chi tiết yêu cầu nằm trong [docs/requirements/README.md](docs/requirements/README.md). Tài liệu này đang ở trạng thái dự thảo để nhóm rà soát.

## Yêu cầu cài đặt

- Docker Desktop để chạy bằng Docker Compose.
- Node.js và npm nếu chạy frontend trực tiếp.
- Python 3.11 trở lên nếu chạy backend trực tiếp.
- **ODBC Driver 18 for SQL Server** nếu chạy backend trực tiếp trên Windows. Thiếu driver này, backend báo lỗi không tìm thấy driver khi kết nối database.
- `bash` (Git Bash hoặc WSL) và `sqlcmd` để chạy `database/init.sh` sau khi nhóm hoàn thành các script SQL.

Không commit `.env`, `frontend/.env.local` hoặc mật khẩu thật lên Git. Dùng `.env.example` làm mẫu cấu hình.

## Chạy frontend

Từ thư mục gốc dự án, chạy:

```powershell
cd frontend
npm install
npm run dev
```

Mở địa chỉ Vite hiển thị trong terminal, thường là `http://localhost:5173`. Proxy `/api` chuyển request tới `http://localhost:8000`; có thể đổi bằng biến `VITE_PROXY_TARGET`.

## Chạy bằng Docker Compose

1. Tạo file cấu hình cục bộ:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Cập nhật mật khẩu SQL Server và `JWT_SECRET_KEY` trong `.env`. Mật khẩu SQL Server cần đủ mạnh (từ 8 ký tự, có chữ hoa, chữ thường, số và ký tự đặc biệt), nếu không container database sẽ không khởi động.
3. Từ thư mục gốc, chạy:

   ```powershell
   docker compose up --build
   ```

Các địa chỉ mặc định:

| Dịch vụ    | Địa chỉ                      |
| ---------- | ---------------------------- |
| Web        | `http://localhost:3000`      |
| API        | `http://localhost:8000`      |
| Swagger    | `http://localhost:8000/docs` |
| SQL Server | `localhost,1433`             |

Docker Compose khởi động các dịch vụ nhưng **không tự chạy script khởi tạo database**. Các file SQL hiện đang trống; sau khi nhóm hoàn thành chúng, cần chạy `database/init.sh` để tạo schema, bảng và dữ liệu mẫu. Muốn làm lại database từ đầu: `docker compose down -v`, chạy lại Compose rồi chạy lại `init.sh`.

## Chạy backend trực tiếp

Backend cần SQL Server đang chạy. Trong PowerShell, từ thư mục gốc:

```powershell
docker compose up -d db
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:JWT_SECRET_KEY = "chuoi-bi-mat-dai-va-ngau-nhien"
$env:MSSQL_HOST = "localhost"
$env:MSSQL_PORT = "1433"
$env:MSSQL_DB = "FamilyConnect"
$env:MSSQL_USER = "sa"
$env:MSSQL_SA_PASSWORD = "mat-khau-sql-server-cua-ban"
uvicorn app.main:app --reload
```

PowerShell không tự nạp biến trong `.env` khi chạy Uvicorn trực tiếp, nên cần khai báo các biến trước khi chạy. Khi backend chạy trong Docker Compose, hostname của SQL Server là `db`. Biến `MSSQL_SA_PASSWORD` giữ mật khẩu của tài khoản đang dùng, nên khi nối DB chung bằng `app_backend`, đổi `MSSQL_USER` và mật khẩu tương ứng. Các API cần database chỉ hoạt động sau khi schema đã được tạo.

## Database

ERD hiện mô tả các bảng dự kiến:

| Schema      | Bảng                                                            |
| ----------- | --------------------------------------------------------------- |
| `core`      | `Users`, `Families`, `Branches`, `MemberVerifications`          |
| `genealogy` | `Members`, `ParentChild`, `Marriages`                           |
| `community` | `Posts`, `Comments`, `Reactions`, `Events`, `EventParticipants` |
| `reports`   | `AuditLog`                                                      |
| `heritage`  | `Items`                                                         |

Quy ước chung:

- Gọi bảng theo dạng `schema.TenBang`, ví dụ `genealogy.Members`.
- Khóa chính kiểu `UNIQUEIDENTIFIER` tên `Id` (riêng `core.Users` là `UserId`), khóa ngoại tên `<Bang>Id`, mọi bảng có `CreatedAt`.
- Model SQLAlchemy phải khai báo schema, ví dụ `__table_args__ = {"schema": "genealogy"}`; nếu thiếu, backend báo `Invalid object name`.
- Mọi file SQL phải chạy lại nhiều lần không lỗi (kiểm tra `IF OBJECT_ID(...) IS NULL` trước `CREATE TABLE`).

Các script được dự kiến chạy theo thứ tự `00_schemas.sql` đến `06_heritage.sql`, sau đó `database/seed/01_seed.sql`. Xem [database/README.md](database/README.md) để biết chi tiết. Khi sửa cấu trúc đã được áp dụng, nhóm nên thêm script patch mới (ví dụ `07_patch_xxx.sql`) thay vì sửa file đã chạy.

### Khởi tạo database sau khi có SQL

Cần `bash`, `sqlcmd` và các biến kết nối. Chạy từ thư mục gốc trong Git Bash hoặc WSL:

```bash
export MSSQL_HOST=localhost
export MSSQL_PORT=1433
export MSSQL_USER=sa
export MSSQL_SA_PASSWORD='mat-khau-sql-server-cua-ban'
export MSSQL_DB=FamilyConnect
bash database/init.sh
```

## Làm việc nhóm trên database

Mỗi thành viên làm trên nhánh Git riêng (ví dụ `db/genealogy`), chỉ sửa file được giao, sau đó mở Pull Request để nhóm review trước khi merge vào `main`. Trước khi mở Pull Request, dựng lại từ database trống (`docker compose down -v` rồi chạy lại) và đảm bảo không có lỗi.

**DB chung qua ZeroTier** dùng để kiểm tra tích hợp giữa các phần, không dùng làm bản demo:

- Người 1 chạy `database/shared/06_permissions.sql` bằng tài khoản `sa` để tạo tài khoản theo từng schema (`dev_core`, `dev_genealogy`, `dev_community`, `dev_reports`, `dev_seed`, `app_backend`). Đổi toàn bộ mật khẩu mẫu trước khi chạy.
- Mỗi người chạy file SQL của mình lên DB chung bằng tài khoản được cấp.
- Mọi thay đổi trên DB chung phải được ghi lại bằng file SQL trong Git; Git là bản chuẩn của cấu trúc database.
- Bản demo cuối chạy hoàn toàn bằng Docker Compose và script trong Git, không phụ thuộc DB chung.

## API hiện có

- `GET /health`: kiểm tra backend.
- `POST /api/auth/register`: đăng ký và nhận JWT.
- `POST /api/auth/login`: đăng nhập và nhận JWT.
- `GET /api/auth/me`: lấy tài khoản hiện tại; cần header `Authorization: Bearer <access_token>`.

API gia phả, cộng đồng, sự kiện, di sản, dashboard và quản trị chưa được triển khai đầy đủ.

## Phân công database

| Thành viên | Phần việc dự kiến                                                                |
| ---------- | -------------------------------------------------------------------------------- |
| 1          | `00_schemas.sql`, `01_core.sql`, `05_late_foreign_keys.sql`, review Pull Request |
| 2          | `02_genealogy.sql` (truy vấn cây gia phả, tổ tiên, hậu duệ)                      |
| 3          | `03_community_events.sql`                                                        |
| 4          | `database/seed/01_seed.sql`                                                      |
| 5          | `04_reports_ops.sql`, `06_heritage.sql`, view và stored procedure báo cáo        |
