# SQL Server / T-SQL
Đã có mã tạo CSDL trong 01_create_database.sql. Các script còn lại là khung TODO, chưa có bảng/dữ liệu/thủ tục thực tế.

## Các nhóm chạy
1. Thiết lập: 01_create_database → 02_create_tables → 03_constraints_indexes → 04_seed_data.
2. Đối tượng nghiệp vụ: 05_views → 06_functions → 07_stored_procedures → 08_triggers.
3. Minh họa/tra cứu: 09_transactions và 10_reports, chạy có chọn lọc sau khi đọc tác động.
4. Quyền: 11_security do DBA cấu hình tài khoản riêng.
5. Vận hành: 12_backup và 13_restore chạy riêng theo docs/backup-restore.md; KHÔNG chạy tự động cùng migration.
6. Kiểm thử: database/tests/ chỉ chạy trên database thử.
Script phải chọn rõ USE FamilyConnectDB khi viết; không dựa vào database đang chọn ngẫu nhiên. GO dùng trong SSMS, không gửi qua pyodbc. File .bak, .mdf, .ldf không commit. SSMS 22 là công cụ, cần SQL Server Database Engine riêng. Ghi lại SELECT @@VERSION khi nghiệm thu; số 22 của SSMS không xác định phiên bản engine.
