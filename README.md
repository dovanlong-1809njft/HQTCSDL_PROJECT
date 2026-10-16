# HQTCSDL_PROJECT

Đồ án môn Hệ quản trị cơ sở dữ liệu (SQL Server, T-SQL)

## Thành viên

| STT | Họ và tên             | MSSV         | Vai trò    |
| --- | --------------------- | ------------ | ---------- |
| 1   | Đỗ Văn Long           | 054205002454 | Leader     |
| 2   | Phạm Lê Ngọc Hân      | 082306014560 | Thành viên |
| 3   | Nguyễn Võ Phương Uyên | 058306001251 | Thành viên |
| 4   | Đoàn Minh Đăng        | 091205011073 | Thành viên |
| 5   | Nguyễn Duy Long       | 060206005525 | Thành viên |

# FamilyConnect 
## Công nghệ
Python/FastAPI; HTML/CSS/JavaScript + Bootstrap; SQL Server/T-SQL và SSMS 22; pyodbc/ODBC 18. Web responsive/PWA phục vụ Android/iOS/Windows. AI dùng embedding + API LLM. Một backend chia module, chưa có app native hay HA thực tế.

## Thư mục
- backend/: API, nghiệp vụ, truy xuất CSDL, tích hợp AI, jobs nhắc lịch.
- frontend/: trang web, CSS/JS, khung PWA.
- database/: T-SQL thiết lập, nghiệp vụ, kiểm thử và vận hành.
- docs/: yêu cầu, thiết kế, phân công, lịch và minh chứng.
- tests/: khung test Python; scripts/: công cụ hỗ trợ.
- .github/: kiểm tra cấu trúc/cú pháp và mẫu làm việc nhóm.
Danh sách toàn bộ tệp: docs/structure-inventory.md.

## Xem giao diện khởi đầu
mở terminal gõ lệnh :py -m http.server 5500 --directory .\FamilyConnect\frontend 
rồi mở link http://localhost:5500/pages/dashboard.html.
Không cần cài backend hoặc SQL Server cho bước giao diện này. Đọc docs/FRONTEND_STEP1.md.
# Frontend — giao diện web
  đã có giao diện/tương tác dữ liệu mẫu; Python chỉ chạy ở máy chủ; trình duyệt dùng HTML/CSS/JavaScript.

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

*****************lưu ý dây là phần giao diện sử dụng AI tham khảo xây dựng, môn học không đặt nặng phần giao diện nhưng vấn đề thật sự là backend và database ********************************
