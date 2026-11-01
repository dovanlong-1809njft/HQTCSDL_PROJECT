# Cơ sở dữ liệu

T-SQL cho SQL Server 2025; hiện có 22 bảng thuộc 5 schema. ERD: docs/erd/README.md.

Thứ tự chạy: 00_schemas, 01_core, 02_genealogy, 03_community_events, 04_reports_ops, 05_late_foreign_keys, 06_heritage, 07_migrate_member_occupation, sau đó seed/01_seed.sql.

Cần SQL Server, bash và sqlcmd. Đặt MSSQL_HOST, MSSQL_PORT, MSSQL_USER, MSSQL_SA_PASSWORD, MSSQL_DB rồi chạy bash database/init.sh từ thư mục gốc. Seed chỉ có dữ liệu giả. Migration chuyển Occupation cũ sang WorkHistories nếu cột còn tồn tại. MemberTreePaths chưa nằm trong schema hiện tại.
