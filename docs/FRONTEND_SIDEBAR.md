# Sidebar thu gọn/mở rộng — FamilyConnect tham khảo từ mã nguồn mở  link : https://21st.dev/@andrewlu0/components/sidebar/sidebar-demo

## Mục tiêu

Triển khai thanh điều hướng **chung về thiết kế và hành vi** cho 12 trang chức năng bằng **HTML/CSS/JavaScript thuần**. Giữ nguyên các chức năng và khung giao diện đã có. Không cần React, Tailwind, Next.js hoặc Framer Motion.

## Các file được thêm

- `frontend/assets/css/sidebar.css`: CSS cho icon rail, trượt khi mở rộng, hiệu ứng nhãn, nút ghim, responsive.
- `frontend/assets/js/core/sidebar.js`: JavaScript quản lý hover/focus/ghim và lưu trạng thái vào trình duyệt.
- `docs/FRONTEND_SIDEBAR.md`: Tài liệu này.

## Các file được chỉnh sửa

Từng file HTML trong `frontend/pages/` **ngoại trừ** `login.html` và `register.html` được thêm liên kết tới CSS/JS, nút ghim và phần tử chứa tên từng mục menu (`.nav-text`). Không thay đổi nội dung của chức năng từng trang. 12 trang có sidebar hoạt động thống nhất nhờ sử dụng cùng hai tệp CSS/JS; tuy nhiên phần HTML điều hướng vẫn nằm trong mỗi trang, chưa được tách thành một file component động.

## Hoạt động trên máy tính (rộng hơn 1023px)

1. Sidebar mở đầu ở dạng **dải biểu tượng rộng 3.05rem** (tương đương khoảng 48,8px với kích thước chữ gốc 16px).
2. Rê chuột vào sidebar → rộng **15rem** (240px), tên các mục menu xuất hiện.
3. Rời chuột → sidebar tự thu gọn (nếu chưa ghim).
4. Nhấn nút **Ghim** (biểu tượng ghim gần logo) → giữ rộng 15rem ngay cả khi di chuột ra khỏi sidebar. Nhấn lại để bỏ ghim.
5. Trạng thái ghim được lưu trong `localStorage` với khóa `familyconnect.sidebar.pinned.v1` và dùng lại sau khi chuyển trang / F5. Nếu trình duyệt chặn lưu trữ, tính năng ghim vẫn hoạt động trong trang đang mở.
6. Khi dùng Tab để di chuyển bàn phím, sidebar sẽ mở khi có focus bên trong và thu gọn sau khi focus rời đi.
7. Menu mở rộng **phủ lên nội dung** chứ không đẩy nội dung sang ngang: nội dung luôn chừa mép trái 3.05rem.
8. Khi không chạy JavaScript, sidebar vẫn hiển thị theo giao diện ban đầu để tránh mất khả năng điều hướng.

## Điện thoại và máy tính bảng (rộng tối đa 1023px)

- Giữ menu kéo từ trái hiện tại của `frontend/assets/js/core/ui.js`.
- Nhấn nút Menu trên topbar để mở, nhấn × / vùng nền tối / Escape để đóng.
- Sidebar trên điện thoại rộng 260px và luôn hiển thị nhãn; không dùng hover, không hiện nút ghim.
- Chức năng focus, đóng drawer và khóa tương tác phía dưới thuộc `core/ui.js`, không nằm trong `sidebar.js`.

## Chạy thử tại máy Windows

Mở PowerShell trong thư mục `FamilyConnect/frontend`, rồi chạy:

```powershell
py -m http.server 5500
```

Truy cập `http://localhost:5500/pages/dashboard.html`. Di chuyển chuột sang Sidebar, bấm Ghim rồi sang `family.html` để kiểm tra trạng thái được giữ. Nhấn F5 và thử lại. Với chế độ Device Toolbar của trình duyệt, thử chiều rộng 375px, 768px và 1024px. Kiểm tra riêng trên `genealogy.html`, `community.html`, `reports.html` và `admin.html` vì đây là các trang có bố cục phức tạp.

## Chú ý khi gộp code nhóm

- Khi tạo trang mới có Sidebar, phải nhúng `sidebar.css` và `core/sidebar.js`, sử dụng `id="app-sidebar"` và `id="sidebar-pin"` đúng quy ước, đặt tên menu trong `.nav-text`.
- Nếu có thêm/xóa một mục menu, hãy cập nhật menu trên **tất cả** trang đang có sidebar. Tách menu HTML thành một component chung là bước cải tiến tiếp theo, chưa nằm trong bản cập nhật này.
- Không đưa dữ liệu thật hoặc mã thông báo đăng nhập vào `localStorage` chỉ vì Sidebar đã dùng `localStorage` để lưu sở thích giao diện.
- CSS có `prefers-reduced-motion` để tắt hiệu ứng khi người dùng yêu cầu giảm chuyển động.
