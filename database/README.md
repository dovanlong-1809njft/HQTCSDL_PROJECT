# Cơ sở dữ liệu

Thư mục này chứa các script T-SQL cho SQL Server 2025. ERD hiện là thiết kế chung của nhóm và mô tả 14 bảng thuộc 5 schema; xem [sơ đồ ERD](../docs/erd/README.md).

## Phân chia file

1. `schema/00_schemas.sql`: tạo database và các schema `core`, `genealogy`, `community`, `reports`, `heritage`.
2. `schema/01_core.sql`: các bảng tài khoản, gia đình, chi nhánh và xác minh thành viên.
3. `schema/02_genealogy.sql`: thành viên và các quan hệ trong gia phả.
4. `schema/03_community_events.sql`: bài viết, bình luận, reaction, sự kiện và RSVP.
5. `schema/04_reports_ops.sql`: nhật ký hệ thống và đối tượng báo cáo.
6. `schema/05_late_foreign_keys.sql`: khóa ngoại cần tạo sau khi có bảng gia phả.
7. `schema/06_heritage.sql`: tài liệu, câu chuyện và ảnh gia đình.
8. `seed/01_seed.sql`: dữ liệu mẫu.

**Lưu ý:** các file SQL hiện đang trống để thành viên trong nhóm tự bổ sung. Vì vậy chưa chạy được phần khởi tạo database. Sau khi hoàn thành, cần chạy theo thứ tự trên; seed chạy cuối cùng.

## Chạy script sau khi nhóm hoàn thành

Cần có SQL Server đang chạy, cùng `bash` và `sqlcmd`. Từ thư mục gốc dự án, cấu hình các biến kết nối rồi chạy:

```bash
export MSSQL_HOST=localhost
export MSSQL_PORT=1433
export MSSQL_USER=sa
export MSSQL_SA_PASSWORD='mat-khau-sql-server-cua-ban'
export MSSQL_DB=FamilyConnect
bash database/init.sh
```

Trên Windows có thể chạy lệnh trong Git Bash hoặc WSL. Nếu dùng SSMS, bật SQLCMD Mode và khai báo `:setvar DB_NAME "FamilyConnect"` ở đầu mỗi script, sau đó chạy các file theo đúng thứ tự.
