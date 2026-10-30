# Kiểm thử FamilyConnect

Nhóm dự kiến kiểm thử theo ba hướng: database, API và hiệu năng. Hiện chưa có file test; nhóm sẽ bổ sung sau khi hoàn thành schema và endpoint tương ứng.

- Kiểm thử database: dự kiến kiểm tra constraint, truy vấn, transaction, quyền và khả năng chạy lại script.
- Kiểm thử API: dự kiến kiểm tra endpoint, xác thực và phân quyền bằng pytest.
- Kiểm thử hiệu năng: dự kiến so sánh truy vấn trước/sau index và lưu kết quả đo.

> **Lưu ý:** Chỉ chạy kiểm thử database trên database thử nghiệm riêng. Không chạy test có thao tác xóa hoặc sửa dữ liệu trên database đang dùng.
