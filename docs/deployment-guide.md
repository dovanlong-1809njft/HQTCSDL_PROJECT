# Cài đặt và triển khai

## Trạng thái hiện tại
API GET /health có mã nền; Frontend hiện đã có 12 trang ứng dụng và hai trang Đăng nhập/Đăng ký **mô phỏng bằng trình duyệt**. Chưa kết nối CSDL, chưa mount frontend vào FastAPI, chưa có API nghiệp vụ; Docker/PWA chưa chạy hoàn chỉnh. Hướng dẫn bên dưới tách việc hiện có với mục tiêu.

## Môi trường
Python 3.11+, SQL Server Database Engine, SSMS 22, Microsoft ODBC Driver 18 và Git. Ghi SELECT @@VERSION để biết engine thực tế. Python có thể chạy từ VS Code hoặc terminal.

## Xem khung hiện có
Tại gốc: python scripts/check_structure.py
Tạo môi trường ảo và cài backend/requirements.txt. Tại backend chạy: python -m uvicorn app.main:app --reload
Mở http://127.0.0.1:8000/health và /docs. /health không xác nhận CSDL.
Tại frontend chạy: `python -m http.server 5500`, rồi mở `http://127.0.0.1:5500/`. Từ bản V7, `index.html` chuyển thẳng tới `pages/login.html` nếu chưa có phiên dùng thử và tới `pages/dashboard.html` nếu đã có phiên. Đăng nhập/đăng xuất ở giai đoạn này chỉ là mô phỏng trong trình duyệt, chưa có Backend xác thực. Các trang khác có giao diện và tương tác mẫu, không còn chỉ là giữ chỗ.

## Mục tiêu sau khi lập trình
1. Chép .env.example thành .env ở gốc; B triển khai nạp file theo đường dẫn gốc, hiện config.py chưa nạp.
2. A viết/chạy script theo database/README.md. Không chạy backup/restore cùng migration.
3. B cài driver, triển khai kết nối và health readiness CSDL riêng; không chia sẻ tài khoản DBA cho app.
4. Backend mount frontend cùng origin và đăng ký router /api/v1; giữ /docs để test.
5. D hoàn thiện manifest/icons/service worker, HTTPS khi dùng qua điện thoại; localhost trên điện thoại là chính điện thoại, không phải máy chủ.
6. E build Docker sau khi hoàn thiện Dockerfile/Compose; cài ODBC trong image, volume upload bền vững. DB_SERVER trong container phải trỏ đúng máy/instance; localhost của container là container.
7. Chạy script index AI khi đã có model và dữ liệu; thử key/timeout trước buổi demo.
8. Kiểm tra ứng dụng từ máy thứ hai, quyền theo gia đình, upload, backup/restore và test hai phiên SSMS.

Thông báo nhắc lịch dùng một worker hoặc tác vụ định kỳ một instance; chống trùng trong CSDL. Không chạy một scheduler không kiểm soát ở mỗi web worker.
Docker healthcheck/restart không chứng minh HA. Chi tiết phạm vi NF08 tại requirements.md.
