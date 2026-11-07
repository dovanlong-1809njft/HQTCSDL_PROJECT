# Cơ sở dữ liệu FamilyConnect

Thư mục này chứa toàn bộ mã nguồn T-SQL (tương thích với SQL Server 2019 / 2022 / 2025 và SSMS 2022).

## 1. Cấu trúc và thứ tự chạy các file SQL

Các script được thực thi tự động theo đúng thứ tự thư mục sau:

1. **`schema/`** — Khởi tạo Database, Schema, Bảng, Ràng buộc và Index:
   - `00_schemas.sql`: tạo database và 5 schema (`core`, `genealogy`, `community`, `reports`, `heritage`).
   - `01_core.sql`: tài khoản, dòng họ, chi nhánh, xác minh thành viên, cấu hình hệ thống.
   - `02_genealogy.sql`: thành viên, quan hệ cha-con, hôn nhân, học vấn (`Educations`), công tác (`WorkHistories`).
   - `03_community_events.sql`: bài viết, ảnh bài viết, bình luận, cảm xúc, báo cáo vi phạm, sự kiện, nhắc hẹn, thư viện ảnh, RSVP.
   - `04_reports_ops.sql`: nhật ký hệ thống (`AuditLog`) và báo cáo tổng quan.
   - `05_late_foreign_keys.sql`: khóa ngoại chéo giữa `core` và `genealogy`.
   - `06_heritage.sql`: tư liệu di sản (`Items`) và vinh danh (`Honors`).
   - `07_ai_assistant.sql`: đoạn văn bản & Vector ngữ nghĩa (`KnowledgeChunks`) và lịch sử hỏi đáp AI (`AiChatMessages`).
2. **`views/`** (`01`..`05`): các View và Function (Scalar / Table-Valued Function) theo từng thành viên.
3. **`procedures/`** (`01`..`05`): các Stored Procedure nghiệp vụ.
4. **`triggers/`** (`01`..`05`): các Trigger kiểm tra ràng buộc và đồng bộ tự động.
5. **`seed/01_seed.sql`**: dữ liệu mẫu dùng chung cho toàn bộ các bảng (chạy lại nhiều lần không lỗi).

---

## 2. Khởi tạo & Test trực tiếp bằng SSMS trên Windows (Không cần Docker)

Nếu máy bạn đã cài sẵn SQL Server trên Windows (`MSSQLSERVER` hoặc `SQLEXPRESS`) và **SSMS (SQL Server Management Studio)**, bạn có thể tạo toàn bộ Database và test các hàm T-SQL mà **không cần bật Docker**:

### Bước 1: Tạo Database & nạp toàn bộ bảng + hàm + dữ liệu mẫu (1 lệnh duy nhất)

Mở Terminal **PowerShell** tại thư mục gốc dự án trong VSCode và chạy:

```powershell
# Trường hợp SSMS kết nối bằng Server name là "localhost" (Windows Authentication):
.\database\init.ps1

# Trường hợp SSMS kết nối bằng ".\SQLEXPRESS":
.\database\init.ps1 -Server ".\SQLEXPRESS"

# Trường hợp dùng tài khoản SQL (ví dụ sa):
.\database\init.ps1 -Server "localhost,1433" -User "sa" -Password "MatKhauCuaBan"
```

> Mỗi khi bạn sửa hoặc viết thêm View / Function / Stored Procedure / Trigger, bạn có thể chạy lại `.\database\init.ps1` (hoặc chạy lẻ từng file bằng `sqlcmd -S localhost -E -C -b -I -d FamilyConnect -v DB_NAME="FamilyConnect" -i <duong-dan-file.sql>`).

### Bước 2: Mở SSMS để kiểm tra và chạy kịch bản Test

1. Mở SSMS, kết nối vào Server của bạn, bấm chuột phải vào **Databases -> Refresh** sẽ thấy Database **`FamilyConnect`** đã có sẵn đầy đủ bảng, dữ liệu mẫu, Function và Stored Procedure.
2. **Cách chạy các file test có sẵn:**
   - Mở trực tiếp file kịch bản kiểm thử trong thư mục [`tests/database/`](../tests/database/) (ví dụ: [`tests/database/test_05_ai_vector_ssms.sql`](../tests/database/test_05_ai_vector_ssms.sql)) trên SSMS và nhấn **F5 (Execute)** — không cần bật chế độ đặc biệt nào.
3. **Cách chạy lẻ 1 file trong `database/` trực tiếp trên cửa sổ SSMS:**
   - Vì các file trong `database/` dùng biến `$(DB_NAME)`, nếu mở trực tiếp trên SSMS hãy vào menu **Query $\rightarrow$ SQLCMD Mode**, thêm dòng `:setvar DB_NAME "FamilyConnect"` ở đầu cửa sổ Query rồi nhấn **F5**.

---

## 3. Khởi tạo bằng Bash (Linux / macOS / Git Bash / Docker)

```bash
export MSSQL_HOST=localhost
export MSSQL_PORT=1433
export MSSQL_USER=sa
export MSSQL_SA_PASSWORD='mat-khau-sql-server-cua-ban'
export MSSQL_DB=FamilyConnect
bash database/init.sh
```
