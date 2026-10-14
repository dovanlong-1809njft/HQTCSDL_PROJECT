# Thay đổi cấu trúc v2 — 14/10/2026

- Giữ tên/thư mục cũ để nhóm dễ đối chiếu; mở rộng các module còn thiếu thay vì đổi framework.
- Bổ sung router/schema/service/repository cho media; hoàn thiện các lớp còn thiếu của users/directory/admin/notifications/dashboard/heritage/AI.
- Bổ sung permissions, embedding client, semantic search service, report service và jobs nhắc lịch.
- Bổ sung trang hồ sơ/thông báo/báo cáo và JavaScript tương ứng; các trang vẫn giữ chỗ. Nạp responsive.css vào HTML.
- Bổ sung SQL quyền, backup, restore và test gia phả/quyền/phục hồi. Chưa viết DDL/nghiệp vụ.
- Thiết kế từ 20 lên 27 bảng: bỏ quan hệ đa hình media, thêm bảng liên kết, phiên, AI chunks, cấu hình và kiểm duyệt.
- Chuẩn hóa API có family_id, đổi RSVP sang PUT, AI theo gia đình.
- Đồng bộ phân công A–E và một kế hoạch 21 ngày; không mặc định số người.
- Docker/PWA/backup trở thành việc có lịch; HA/native được ghi rõ còn chưa đáp ứng.
- Có công cụ kiểm kê/cú pháp và sơ đồ Mermaid mục tiêu; không tạo test giả assert True.

Giải nén vào thư mục mới để so sánh. Nếu repo đã có code do nhóm viết, không ghi đè hàng loạt bằng khung TODO. ZIP này là bản cập nhật cấu trúc, không phải bản nâng cấp ứng dụng đã chạy.
