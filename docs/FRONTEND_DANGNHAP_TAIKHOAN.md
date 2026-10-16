# FamilyConnect — Đăng nhập, đăng ký và menu tài khoản Frontend V4 (bản update/sửa lỗi v4) 

## Mục tiêu và phạm vi

Trang `frontend/index.html` là lối vào ứng dụng, chuyển đến `pages/login.html` nếu chưa có phiên dùng thử. Sau khi đăng nhập sẽ mở Dashboard; 12 trang ứng dụng được điều hướng về `login.html` khi chưa đăng nhập trong chế độ mô phỏng. Đăng xuất từ menu avatar góc phải sẽ xóa phiên dùng thử và chuyển về trang Đăng nhập.

**LƯU Ý BẢO MẬT:** Xác thực hiện được mô phỏng hoàn toàn bằng JavaScript và localStorage, **không an toàn để triển khai trên Internet**. Không xem điều hướng/kiểm tra tại trình duyệt là kiểm soát truy cập thật; Backend phải xác minh phiên và phân quyền trên mọi API. Không lưu mật khẩu thật hay token thật trong localStorage. Không đưa mật khẩu của Google/Facebook vào trang mẫu.

## Kiểm tra giao diện ngay

Tại thư mục `frontend/`, chạy:

```powershell
py -m http.server 5500
```

Mở `http://localhost:5500/` sẽ thấy trang Đăng nhập.

Tài khoản dùng thử: `demo@familyconnect.local` / `Demo@12345`. Nhấn “Điền tài khoản mẫu” để điền sẵn. Tài khoản trên là dữ liệu minh họa công khai, **không phải mật khẩu bảo mật**.

Nhấn “Đăng ký” để tạo tài khoản **chỉ trong trình duyệt hiện tại**. Bản mẫu lưu tên, email, tài khoản và mã dẫn xuất PBKDF2 của mật khẩu (không ghi nguyên văn mật khẩu) ở localStorage; việc này **không thay thế cơ chế bảo mật của Backend**. Trang Đăng nhập chấp nhận email hoặc tên tài khoản vừa đăng ký. Tài khoản mẫu và dữ liệu gia đình dùng chung localStorage nên chưa có tính riêng tư giữa những người dùng máy/trình duyệt.

Google (Gmail), Facebook: Nút mới chỉ thông báo rằng OAuth chưa được tích hợp. Khi triển khai thật, dùng OAuth/OpenID Connect với PKCE, cấu hình ứng dụng tại Google/Facebook và chỉ xử lý đăng nhập qua Backend. **Không tự viết biểu mẫu giả nhận mật khẩu Google/Facebook.**

Quên mật khẩu: Đây là màn hình giải thích trạng thái; chưa gửi email, chưa tạo token khôi phục. Khi có Backend, triển khai luồng xác minh địa chỉ và đặt lại mật khẩu bằng token thời hạn ngắn.

## Thay ảnh nền đăng nhập

Mở `frontend/assets/css/auth-page.css`, tìm:

```css
:root { --auth-wallpaper: none; }
```

Khi có ảnh thật, chép ảnh vào `frontend/assets/images/login-background.jpg` và sửa:

```css
:root { --auth-wallpaper: url('../images/login-background.jpg'); }
```

Lớp phủ `rgba(255,255,255,.91)` giúp ảnh nền mờ nhẹ và biểu mẫu dễ đọc. Hiện tại không có ảnh nên nền trắng.

## Menu avatar góc trên bên phải

Bấm avatar tròn ở Topbar để mở 3 thao tác:

1. **Xem trang cá nhân** → `profile.html`.
2. **Giao diện Sáng/Tối** → nút gạt qua trái/phải. Chế độ được lưu ở localStorage và áp dụng cho các trang bằng `theme.css`.
3. **Đăng xuất** → xóa phiên dùng thử rồi về `login.html`.

Các màu tối hiện được phủ lên thành phần dùng chung và những khối chính; với 12 trang có nhiều CSS riêng, cần kiểm tra trực quan từng phân hệ để tinh chỉnh thêm màu của bảng, biểu đồ, tooltip.

## File đã bổ sung / chỉnh sửa

- `frontend/pages/login.html`: giao diện đăng nhập.
- `frontend/pages/register.html`: giao diện đăng ký.
- `frontend/index.html`: lối vào ứng dụng.
- `frontend/assets/css/auth-page.css`: định dạng đăng nhập, chỗ thay ảnh nền.
- `frontend/assets/css/account-menu.css`: menu tài khoản kiểu Facebook.
- `frontend/assets/css/theme.css`: màu sáng/tối.
- `frontend/assets/js/core/auth.js`: phiên và tài khoản bản xem trước.
- `frontend/assets/js/modules/auth-page.js`: xử lý biểu mẫu.
- `frontend/assets/js/core/account-menu.js`: nút avatar, bật tắt chủ đề và đăng xuất.
- `frontend/assets/js/core/profile-badge.js`: ảnh đại diện đồng bộ với nút menu.
- 12 file `.html` ứng dụng: nạp các file dùng chung và thay avatar từ liên kết sang nút bấm.

## Checklist thử nghiệm trên máy

- Khi mở `/` hoặc truy cập `pages/genealogy.html` trong phiên chưa đăng nhập → đến trang đăng nhập.
- Đăng nhập bằng demo, mở Dashboard và từng trang → hoạt động.
- Bấm avatar → thấy 3 lựa chọn; bấm “Xem trang cá nhân” → mở profile.
- Gạt Sáng/Tối và F5, chuyển trang → giữ chủ đề.
- Thay avatar tại profile rồi mở menu → avatar đồng bộ.
- Bấm Đăng xuất → về login, không vào trang ứng dụng trước khi đăng nhập lại.
- Google/Facebook/Quên mật khẩu hiển thị thông báo chưa kết nối Backend, không tuyên bố đăng nhập thành công.
- Kiểm tra 375px mobile, 768px tablet, 1440px desktop.

**Trước khi kết nối SQL Server**: Phải thay toàn bộ logic xác thực giả bằng Backend FastAPI + tài khoản lưu trong SQL Server; dùng phiên bảo vệ bằng cookie HttpOnly, Secure, SameSite hợp lý, mật khẩu băm an toàn tại máy chủ, rate limiting, CSRF protection khi dùng cookies; OAuth tích hợp qua nhà cung cấp theo quy trình chuẩn.

## Cảnh báo đồng bộ tài liệu ngày 16/10/2026

**Nhật ký sai lệch và xử lý:** Bản ZIP `FamilyConnect_Frontend(3).zip` từng chứa `<meta http-equiv="refresh" content="0; url=pages/dashboard.html">`, khiến người chưa đăng nhập bị chuyển tới Dashboard trước khi kiểm tra phiên. **Bản V7 (16/10/2026) đã sửa `frontend/index.html`** bằng cách nạp `auth.js` và kiểm tra phiên mẫu trước khi điều hướng: chưa có phiên → Login; có phiên → Dashboard. Cần thử trực tiếp trên trình duyệt; đây không phải xác thực bảo mật phía máy chủ.

Xem thêm: `PROJECT_STATUS.md` và `DOCUMENT_AUDIT.md`.
