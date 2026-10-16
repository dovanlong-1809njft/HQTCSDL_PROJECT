# FamilyConnect 
**Đã triển khai frontend: dashboard dữ liệu mẫu và giao diện chung. Phần lớn dự án còn là bộ khung, chưa phải ứng dụng hoàn chỉnh.** Đọc docs/SCAFFOLD_STATUS.md trước khi chạy.

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

UPDATE LẦN 1
# Frontend — giao diện web
Dashboard và Gia đình của tôi đã có giao diện/tương tác dữ liệu mẫu; các trang còn lại là HTML giữ chỗ. Python chỉ chạy ở máy chủ; trình duyệt dùng HTML/CSS/JavaScript.

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

## Gia đình của tôi — bước 2
Mở pages/family.html. Chỉnh thông tin/ảnh, quản lý thành viên và chi nhánh, lọc thành viên, xem hoạt động. Thay đổi lưu localStorage theo trình duyệt/origin; không dùng dữ liệu thật. Đọc ../docs/FRONTEND_GIADINH.md.

## Cây gia phả — bước 3
Mở pages/genealogy.html. Lọc, thu phóng, đổi hướng, quản lý người/quan hệ, truy vấn cơ bản và xuất SVG. Dùng chung FamilyStore với Gia đình của tôi. Hướng dẫn: ../docs/FRONTEND_CAYGIAPHA.md.

## Danh bạ thành viên — bước 4
Mở pages/directory.html. Tìm/lọc, dạng thẻ/bảng, phân trang, xem và quản lý hồ sơ, xuất CSV. Lời mời/tin nhắn là bản nháp chưa gửi. Xem ../docs/FRONTEND_DANHBA.md.

## Cộng đồng — bước 5
Mở pages/community.html. Bảng tin, bài ảnh/video qua URL/kỷ niệm/khảo sát, cảm xúc, bình luận, lưu bài, thư viện và sinh nhật. Chỉ lưu cục bộ; không đăng hoặc chia sẻ thực tế qua mạng. Xem ../docs/FRONTEND_CONGDONG.md. 
........................xem tiến trình tại mục docs

## Giao diện đăng nhập và tài khoản (V4)
Mở `/` hoặc `pages/login.html` trước khi dùng app. Tài khoản mẫu `demo@familyconnect.local` / `Demo@12345`; có đăng ký tài khoản mô phỏng. Menu avatar trên Topbar có Xem hồ sơ, Sáng/Tối, Đăng xuất.
Google/Facebook và Quên mật khẩu cần Backend xác thực thực tế; xem `../docs/FRONTEND_DANGNHAP_TAIKHOAN.md`. Frontend này không có kiểm soát bảo mật thực.


*****************************************************************************************************************************************************lưu ý dây là phần giao diện sử dụng AI tham khảo xây dựng môn học không đặt nặng phần giao diện nhưng vấn đề thật sự là backend và database********************************************************************************************************************************************************************************************************************************************************************************
