# Frontend bước 1 — 14/10/2026

Đã lập trình kiểu dáng chung, bố cục responsive, menu và dashboard dữ liệu mẫu. Các trang khác vẫn giữ chỗ.

## Các tệp chính
- frontend/assets/css/main.css: màu, chữ, nút, form, sidebar, panel, dialog và toast.
- frontend/assets/css/responsive.css: desktop/tablet/mobile, menu thu gọn.
- frontend/assets/js/core/ui.js: menu, Escape, giữ/khôi phục focus, thông báo.
- frontend/assets/js/main.js: khởi tạo giao diện.
- frontend/pages/dashboard.html: trang tổng quan.
- frontend/assets/js/modules/dashboard.js: hai bộ dữ liệu mẫu, lọc hoạt động, chi tiết sự kiện và RSVP thử.
- frontend/index.html: mở dashboard; các trang giữ chỗ có link quay về dashboard.

## Chạy trên máy của bạn
Mở terminal tại thư mục frontend:

```bash
python -m http.server 5500
```

Nếu Windows dùng lệnh py, chạy `py -m http.server 5500`.
Mở http://localhost:5500 trong trình duyệt. Chỉ cần Python để phục vụ tệp tĩnh; bước này không cần SQL Server, FastAPI hoặc cài thư viện Python ngoài.
Không chạy file .css hay .js riêng. Trình duyệt nạp chúng qua HTML.

## Những việc có thể thử
1. Chọn Gia đình Nguyễn/Lê: số liệu, hoạt động và sự kiện đổi theo dữ liệu mẫu.
2. Lọc bài đăng/tư liệu/thành viên.
3. Mở chi tiết sự kiện, thử xác nhận/hủy tham gia. Dữ liệu chỉ giữ trong bộ nhớ tab, tải lại sẽ mất.
4. Thu nhỏ màn hình: mở menu, đóng bằng nút, vùng ngoài hoặc Escape; dùng Tab để điều hướng.
5. Các liên kết phân hệ khác mở trang giữ chỗ, sẽ lập trình ở bước tiếp theo.

## Kiểm tra đã thực hiện
- JavaScript qua node --check: đạt.
- Chromium headless: trang đầu chuyển dashboard, hai gia đình, bộ lọc, dialog, xác nhận/hủy, Escape, menu và khôi phục focus: đạt.
- Các cỡ viewport 320, 390, 768, 1024, 1440px không tràn ngang. Đây là mô phỏng viewport, chưa phải kiểm tra iOS/Android thật.
- Tất cả URL điều hướng và tài nguyên cục bộ được kiểm tra; không gặp lỗi JavaScript hoặc HTTP 4xx/5xx.
- Đã xem ảnh render desktop/mobile để chỉnh bố cục.

Không có API/DB/auth thật ở bước này. Tài khoản, số liệu, thời gian và sự kiện đều là mẫu. Xác nhận thử không gửi tới máy chủ. PWA chưa hoạt động.

Bước kế tiếp: giao diện đăng nhập/đăng ký cùng account.js, sau đó gia đình và cây gia phả.
