> **Lưu ý 16/10/2026:** Các kết quả dưới đây là ghi chép kiểm tra theo từng bước lịch sử và **không được chạy lại đầy đủ trong đợt rà soát tài liệu**. Để biết trạng thái của ZIP hiện tại, xem `PROJECT_STATUS.md` và `DOCUMENT_AUDIT.md`.
# Kiểm tra gói — frontend bước 2

196 tệp nguồn, 28 thư mục con; bản cập nhật chỉ gồm các tệp frontend/tài liệu thay đổi. Không thay đổi backend/database.
Cú pháp JavaScript, liên kết HTML/ID: đạt. Kho dữ liệu mẫu qua Node VM và luồng DOM qua jsdom: đạt, chi tiết FRONTEND_GIADINH.md.
Chưa kiểm tra hiển thị Chromium, ảnh decode/resize hoặc thiết bị thật trong bước 2. Không dùng kết quả kiểm tra bước 1 để thay cho bước 2.
ZIP kiểm tra CRC và so sánh từng tệp với source đã cập nhật.

## Frontend bước 3 — Cây gia phả
Đã kiểm tra cú pháp, đường dẫn tài nguyên HTML, ID duy nhất, mô phỏng thao tác gia phả và hồi quy trang gia đình. Backend/database không đổi. Chi tiết và giới hạn: FRONTEND_CAYGIAPHA.md.

## Frontend bước 4 — Danh bạ
Đã kiểm tra cú pháp, tài nguyên HTML, mô phỏng thao tác danh bạ và hồi quy hai trang gia đình/gia phả. Không thay đổi backend/database. Chi tiết: FRONTEND_DANHBA.md.

## Frontend bước 5 — Cộng đồng
Đã kiểm tra cú pháp, tài nguyên HTML/SVG, mô phỏng thao tác cộng đồng, hết dung lượng lưu và hồi quy các trang trước. Backend/database không đổi. Chưa xác nhận bố cục/video/giải mã ảnh trong trình duyệt thực tế. Chi tiết: FRONTEND_CONGDONG.md.

## Frontend bước 6 — Sự kiện
Đã kiểm tra cú pháp, HTML, mô phỏng DOM, UTC+7, nội dung .ics, luồng album bằng mock và liên kết Tổng quan. Backend/database không đổi. Chưa kiểm tra trình duyệt/ảnh thật/import lịch thật. Xem FRONTEND_SUKIEN.md.

## Frontend bước 7 — Di sản & tư liệu
Đã kiểm tra cú pháp, HTML/SVG, mô phỏng DOM, tệp TXT UTF-8, bộ sưu tập, số liệu chung và hồi quy các trang trước. Backend/database không đổi. Giới hạn: FRONTEND_DISAN.md.

## Frontend bước 8 — Trợ lý AI
Đã kiểm tra cú pháp, HTML/ID, mô phỏng hội thoại, thống kê/quan hệ/trích ý, TXT, nguồn, lịch sử và hết dung lượng. Các module trước cùng backend/database không đổi. Chưa kiểm tra bố cục/clipboard/ảnh thật; chưa có dịch vụ AI. Xem FRONTEND_TROLYAI.md.

## Frontend bước 9 — Báo cáo & thống kê
Đã kiểm tra cú pháp, HTML/ID, tính số liệu theo UTC+7, bộ lọc, biểu đồ/bảng, CSV và thao tác in được mô phỏng. Xác nhận module trước/backend/database không đổi. Chưa kiểm tra bố cục/in/Excel thật. Xem FRONTEND_BAOCAO.md.

## Frontend bước 10 — Thông báo
Đã kiểm tra cú pháp/HTML, mô phỏng thông báo/giờ yên tĩnh/trạng thái, nạp script HTML thực tế trên mọi trang đã triển khai, huy hiệu và hồi quy các chức năng trước sau thay đổi FamilyStore. Backend/database không đổi. Chưa xác nhận bố cục/native dialog/clipboard thật. Xem FRONTEND_THONGBAO.md.


## Cập nhật Hồ sơ cá nhân
Đã triển khai trang profile.html, profile.css và account.js. Xem FRONTEND_HOSO.md để biết chức năng, giới hạn và kiểm thử. Backend/database không thay đổi.


## Cập nhật Quản trị
Đã triển khai admin.html, admin.css, admin.js. Chi tiết chức năng, giới hạn và kiểm thử: FRONTEND_QUANTRI.md. Backend/database không thay đổi.
