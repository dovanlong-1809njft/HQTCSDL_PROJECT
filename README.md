# FamilyConnect

FamilyConnect là đề tài môn **Hệ quản trị cơ sở dữ liệu**, hướng tới xây dựng nền tảng cộng đồng gia đình số để quản lý gia phả, kết nối thành viên, tổ chức sự kiện và lưu giữ di sản gia đình. Trọng tâm của dự án là thiết kế và khai thác cơ sở dữ liệu SQL Server; ứng dụng web dùng để minh họa các luồng nghiệp vụ.

## Trạng thái dự án

- Frontend có giao diện đăng nhập, đăng ký và trang tổng quan cơ bản.
- Backend có health check và API đăng ký, đăng nhập, xem tài khoản hiện tại.
- ERD và T-SQL hiện mô tả 22 bảng thuộc 5 schema. Xem [sơ đồ ERD](docs/erd/README.md).
- Script SQL trong database/schema/ và dữ liệu mẫu trong database/seed/ đã được bổ sung. API nghiệp vụ ngoài xác thực vẫn đang được phát triển.
- Các thư mục kiểm thử API, database và hiệu năng chưa có test thực thi. Xem [kế hoạch kiểm thử](tests/README.md).

## Công nghệ

- Frontend: React, Vite, JavaScript, Tailwind CSS, React Router, Axios, TanStack Query, React Hook Form.
- Backend: FastAPI, SQLAlchemy, JWT.
- Database: Microsoft SQL Server 2025 và T-SQL.
- Đóng gói môi trường phát triển: Docker Compose.
- React Flow và Recharts hiện có trong dependencies, dành cho phần cây gia phả và biểu đồ khi các chức năng đó được triển khai.

## Cấu trúc dự án

```text
apps/
  backend/               # API FastAPI tổ chức theo DDD (core, domains, shared)
  worker/                # Tác vụ chạy ngầm (APScheduler/Celery)
  web/                   # Ứng dụng web React (feature-based: auth, dashboard, ...)
  mobile/                # Khung dự án ứng dụng di động
packages/
  api-contract/          # Hợp đồng API / OpenAPI dùng chung
  mock-data/             # Dữ liệu JSON giả lập dùng chung
database/
  schema/                # Các script tạo schema và bảng (00..06)
  views/                 # Các script tạo View
  procedures/            # Các script Stored Procedure
  seed/                  # Script dữ liệu mẫu
  shared/                # Script chỉ chạy trên DB chung (phân quyền theo schema)
  perf/                  # Phân tích Execution Plan và tối ưu truy vấn
  init.sh                # Chạy các file SQL theo thứ tự tên
infra/
  docker/                # Dockerfile (đa target), nginx.conf, docker-compose.yml
docs/
  requirements/          # Yêu cầu, vai trò và use case
  architecture/          # Kiến trúc hệ thống
  erd/                   # ERD thiết kế
  api-spec/              # Đặc tả API
tests/                   # Kiểm thử e2e, api, database và performance
```

Chi tiết yêu cầu nằm trong [docs/requirements/README.md](docs/requirements/README.md). Tài liệu này đang ở trạng thái dự thảo để nhóm rà soát.

## Yêu cầu cài đặt

- Docker Desktop để chạy bằng Docker Compose.
- Node.js và npm nếu chạy frontend trực tiếp.
- Python 3.11 trở lên nếu chạy backend trực tiếp.
- **ODBC Driver 18 for SQL Server** nếu chạy backend trực tiếp trên Windows. Thiếu driver này, backend báo lỗi không tìm thấy driver khi kết nối database.
- `bash` (Git Bash hoặc WSL) và `sqlcmd` để chạy `database/init.sh` sau khi nhóm hoàn thành các script SQL.

Không commit `.env`, `apps/web/.env.local` hoặc mật khẩu thật lên Git. Dùng `.env.example` làm mẫu cấu hình.

## Chạy frontend

Từ thư mục gốc dự án, chạy:

```powershell
cd apps/web
npm install
npm run dev
```

Mở địa chỉ Vite hiển thị trong terminal, thường là `http://localhost:5173`. Proxy `/api` chuyển request tới `http://localhost:8000`; có thể đổi bằng biến `VITE_PROXY_TARGET`.

## Chạy bằng Docker Compose

Chạy từ thư mục gốc dự án (PowerShell):

```powershell
Copy-Item .env.example .env
docker compose --env-file .env -f infra/docker/docker-compose.yml up --build
```

Một lệnh trên sẽ tự động: khởi động SQL Server → chạy `database/schema/*.sql` và `database/seed/*.sql` (service `db-init`) → khởi động backend → khởi động web. Mật khẩu SQL Server cần đủ mạnh (từ 8 ký tự, có chữ hoa, chữ thường, số và ký tự đặc biệt), nếu không container `db` sẽ không khởi động.

| Dịch vụ            | Địa chỉ                      | Ghi chú                                          |
| ------------------ | ---------------------------- | ------------------------------------------------ |
| Web (nginx, build) | `http://localhost:3000`      | Bản build sẵn, cần `--build` lại khi sửa web     |
| Web dev (Vite)     | `http://localhost:5173`      | Chỉ chạy khi thêm `--profile dev`, có hot reload |
| API                | `http://localhost:8000`      | Tự nạp lại khi sửa code trong `apps/backend/app` |
| Swagger            | `http://localhost:8000/docs` |                                                  |
| SQL Server         | `localhost,1433`             | Tài khoản `sa`, mật khẩu lấy từ `.env`           |

Các lệnh thường dùng (thêm tiền tố `docker compose --env-file .env -f infra/docker/docker-compose.yml`):

| Mục đích                          | Lệnh                                     |
| --------------------------------- | ---------------------------------------- |
| Chạy kèm web dev có hot reload    | `--profile dev up --build`               |
| Chạy nền                          | `up -d`                                  |
| Xem log một dịch vụ               | `logs -f backend` (hoặc `db-init`, `db`) |
| Chạy lại script SQL sau khi sửa   | `up db-init`                             |
| Dừng                              | `down`                                   |
| Xóa sạch database, làm lại từ đầu | `down -v` rồi `up --build`               |

Docker Compose khởi động các dịch vụ nhưng không tự chạy script database. Khi SQL Server sẵn sàng, chạy database/init.sh từ Git Bash hoặc WSL để áp dụng schema, migration và seed. docker compose down -v xóa volume database; chỉ dùng khi muốn xóa dữ liệu cục bộ.

- Script SQL được mount từ `database/` nên sửa file xong chỉ cần `up db-init`, không cần build lại.
- Đổi `MSSQL_SA_PASSWORD` sau lần chạy đầu không có tác dụng với database đã tạo; cần `down -v` để tạo lại.
- Kết nối SSMS/Azure Data Studio: server `localhost,1433`, user `sa`, bật **Trust server certificate**.

## Chạy backend trực tiếp

Backend cần SQL Server đang chạy. Trong PowerShell, từ thư mục gốc:

```powershell
docker compose --env-file .env -f infra/docker/docker-compose.yml up -d db
cd apps/backend
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

ERD hiện có 22 bảng thuộc 5 schema:

| Schema    | Bảng                                                                                                               |
| --------- | ------------------------------------------------------------------------------------------------------------------ | ------- |
| core      | Users, Families, Branches, MemberVerifications, SystemConfigs                                                      |
| genealogy | Members, ParentChild, Marriages, Educations, WorkHistories                                                         |
| community | Posts, PostMedia, Comments, Reactions, Events, EventParticipants, EventReminders, EventGalleries, ReportedContents |
| reports   | AuditLog                                                                                                           |
| heritage  | Items, Honors                                                                                                      | `Items` |

Quy ước chung:

- Gọi bảng theo dạng `schema.TenBang`, ví dụ `genealogy.Members`.
- Khóa chính kiểu `UNIQUEIDENTIFIER` tên `Id` (riêng `core.Users` là `UserId`), khóa ngoại tên `<Bang>Id`, mọi bảng có `CreatedAt`.
- Model SQLAlchemy phải khai báo schema, ví dụ `__table_args__ = {"schema": "genealogy"}`; nếu thiếu, backend báo `Invalid object name`.
- Mọi file SQL phải chạy lại nhiều lần không lỗi (kiểm tra `IF OBJECT_ID(...) IS NULL` trước `CREATE TABLE`).

Các script chạy theo thứ tự 00_schemas.sql đến 07_migrate_member_occupation.sql, sau đó database/seed/01_seed.sql. Xem database/README.md. Thay đổi database đã áp dụng cần thêm migration mới, không sửa script lịch sử.

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

Mỗi thành viên làm trên nhánh Git riêng (ví dụ `db/genealogy`), chỉ sửa file được giao, sau đó mở Pull Request để nhóm review trước khi merge vào `main`. Trước khi mở Pull Request, dựng lại từ database trống (`docker compose --env-file .env -f infra/docker/docker-compose.yml down -v` rồi chạy lại) và đảm bảo không có lỗi.

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

| Thành viên | Phần việc dự kiến                                                                                                         |
| ---------- | ------------------------------------------------------------------------------------------------------------------------- |
| 1          | `00_schemas.sql`, `01_core.sql`, `05_late_foreign_keys.sql`, review Pull Request                                          |
| 2          | 02_genealogy.sql: Members, ParentChild, Marriages, Educations, WorkHistories; truy vấn cây gia phả                        |
| 3          | 03_community_events.sql: Posts, PostMedia, Events, EventReminders, EventGalleries, ReportedContents và các bảng liên quan |
| 4          | `database/seed/01_seed.sql`                                                                                               |
| 5          | 04_reports_ops.sql, 06_heritage.sql (Items, Honors), view và stored procedure báo cáo                                     |
