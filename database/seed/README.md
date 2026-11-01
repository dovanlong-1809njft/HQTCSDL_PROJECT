# Dữ liệu mẫu

01_seed.sql chứa dữ liệu giả cho các bảng trong schema hiện tại. Email dùng miền .invalid, password hash là giá trị giả và không dùng để đăng nhập. Script xóa và tạo lại các bản ghi mẫu theo GUID cố định, không đụng tới bản ghi của người dùng khác.

Chạy sau toàn bộ database/schema/*.sql bằng database/init.sh hoặc theo thứ tự trong database/README.md.
