# Sao lưu và khôi phục

TRẠNG THÁI: quy trình mục tiêu, script 12/13 còn là khung. Đầu mối A, phối hợp E.
1. Dùng database demo và dữ liệu giả. Ghi số lượng bản ghi mốc, thời gian, phiên bản ứng dụng.
2. DBA chọn thư mục backup trên máy SQL Server mà tài khoản dịch vụ SQL được ghi, không dùng đường dẫn do người dùng web nhập.
3. Viết/chạy 12_backup.sql, ghi kết quả và giữ .bak ngoài Git.
4. Viết 13_restore.sql: xem logical names, chọn đường dẫn data/log mới, restore sang FamilyConnectRestoreTest; không ghi đè database làm việc.
5. Chạy database/tests/test_restore.sql đã triển khai: so dữ liệu và thử nghiệp vụ mẫu. VERIFYONLY không thay thế thử phục hồi thật.
6. Ảnh/tài liệu nằm ở upload volume: sao lưu volume cùng metadata; tạm dừng ghi hoặc dùng cách chụp nhất quán. Backup SQL đơn lẻ không chứa bytes ảnh.
7. Ghi thời gian phục hồi và mất dữ liệu quan sát được, không tuyên bố RPO/RTO hoặc HA khi chưa có bằng chứng.

Backup/restore không mở thành API công khai. Dữ liệu .bak và upload không đính kèm gói source.
