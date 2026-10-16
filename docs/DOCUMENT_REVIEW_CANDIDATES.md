# Danh sách file ĐỀ XUẤT xem xét — KHÔNG XÓA

| File | Lý do cần xem xét | Quyết định hiện tại |
|---|---|---|
| `docs/sw.js` | Nằm trong tài liệu, trong khi Service Worker dùng cho PWA ở `frontend/sw.js`; khả năng là bản sao/bản đặt nhầm vị trí. Cần đọc nội dung và kiểm tra mọi đường dẫn tham chiếu trước khi quyết định | **Giữ nguyên; cân nhắc xóa hoặc chuyển về đúng chỗ sau khi xác minh** |
| `docs/diagrams/.gitkeep` | `docs/diagrams/` đã có `README.md` và `.mmd`; `.gitkeep` không còn cần thiết để giữ thư mục trống nhưng không gây lỗi | **Giữ; có thể dọn sau** |
| `frontend/assets/icons/.gitkeep` | Thư mục đã có `README.md`; tương tự | **Giữ; có thể dọn sau** |
| `docs/FRONTEND_STEP1.md` | Tài liệu phản ánh thời điểm ban đầu, không phản ánh toàn bộ tiến độ mới | **Giữ như nhật ký lịch sử, không xóa** |
| `docs/FRONTEND_UI_FIXES_V3.md`, `docs/FRONTEND_DARK_MODE_V5.md` | Có vẻ cùng chủ đề giao diện nhưng mô tả hai đợt sửa khác nhau | **Phải giữ để truy lại lịch sử** |
| `docs/CHANGELOG_STRUCTURE.md` và `docs/DEVELOPMENT_HISTORY.md` | Một file ghi thay đổi **cấu trúc v2**, file còn lại ghi dòng thời gian toàn dự án | **Giữ cả hai, không trùng vai trò** |
| `docs/SCAFFOLD_STATUS.md` và `docs/PROJECT_STATUS.md` | Trạng thái cũ theo giai đoạn vs ảnh chụp hiện tại; có thể được hiểu nhầm là trùng lặp | **Giữ, cập nhật lời dẫn/điều hướng để tránh nhầm** |
| `README.md`, `frontend/README.md`, `docs/README.md` | Cùng là README nhưng khác phạm vi | **Giữ đầy đủ** |

**Nếu có đề xuất xóa trong tương lai:** ghi rõ file → lý do → file tham chiếu tới nó → ảnh hưởng → phương án thay thế → xin chủ dự án duyệt. Không xóa chỉ vì file cũ hoặc có tên gần giống.
