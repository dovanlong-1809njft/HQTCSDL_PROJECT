# Frontend — giao diện web
Dashboard đã có giao diện và tương tác dữ liệu mẫu; các trang còn lại là HTML giữ chỗ. Python chỉ chạy ở máy chủ; trình duyệt dùng HTML/CSS/JavaScript.

- pages/family.html: gia đình, nhánh, yêu cầu tham gia và duyệt.
- pages/genealogy.html: người, cha/mẹ-con, hôn nhân, cây và tra cứu quan hệ.
- pages/community.html: bài đăng, bình luận, phản ứng và ảnh.
- pages/events.html: sự kiện, RSVP, người tham gia và album.
- pages/directory.html: tìm kiếm theo tên, nghề nghiệp, địa điểm, thế hệ.
- pages/heritage.html: tư liệu, câu chuyện, người tiêu biểu và thư viện ảnh.
- pages/profile.html: hồ sơ tài khoản; login.html/register.html: xác thực.
- pages/notifications.html: thông báo và nhắc lịch.
- pages/dashboard.html: tổng quan; reports.html: thống kê chi tiết và xuất CSV.
- pages/ai-assistant.html: hỏi đáp, tìm kiếm ngữ nghĩa, tóm tắt và đề xuất.
- pages/admin.html: quản trị hệ thống, kiểm duyệt và cấu hình.

Đề xuất UI: nền sáng, xanh lá đậm, chữ rõ. Desktop có menu trái; mobile menu thu gọn. Cây gia phả có phóng to/thu nhỏ và bảng chi tiết. Dùng Bootstrap 5, vis-network, Chart.js khi lập trình, hiện chưa nhúng các thư viện này.

Dự kiến FastAPI phục vụ frontend cùng origin, /api/v1 cho API. main.py hiện chưa mount frontend. Chạy python -m http.server 5500 trong frontend để xem dashboard; chi tiết tại ../docs/FRONTEND_STEP1.md. PWA chưa hoạt động.
