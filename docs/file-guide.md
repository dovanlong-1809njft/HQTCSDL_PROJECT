# Tên thư mục và phần mở rộng

| Tên | Nghĩa và vai trò |
|---|---|
| backend | Phía máy chủ Python/FastAPI |
| routers | Tiếp nhận yêu cầu API |
| schemas | Khuôn mẫu dữ liệu Pydantic, khác schema CSDL |
| services | Xử lý nghiệp vụ và điều phối |
| repositories | Truy xuất SQL Server |
| core | Xác thực, quyền và lỗi dùng chung |
| db | Kết nối CSDL |
| integrations | Kết nối LLM và embedding |
| jobs | Tác vụ nền nhắc lịch |
| frontend/pages | Các trang giao diện |
| frontend/assets | CSS, JS, ảnh và biểu tượng |
| database | T-SQL; database/tests là kiểm thử CSDL |
| docs | Tài liệu; diagrams chứa mã nguồn sơ đồ |
| tests | Kiểm thử API/Python |
| scripts | Công cụ hỗ trợ phát triển |

.py: mã Python; .sql: T-SQL; .html: cấu trúc giao diện; .css: trình bày; .js: tương tác trình duyệt; .json: dữ liệu/cấu hình; .md: tài liệu Markdown; .mmd: mã nguồn sơ đồ Mermaid; .yml: YAML; .txt: văn bản hoặc danh sách thư viện.
.env.example là mẫu biến môi trường; .gitignore là quy tắc bỏ qua Git; .gitkeep giữ thư mục trống theo quy ước; Dockerfile không có đuôi và mô tả image khi đã viết.

Ví dụ genealogy_repository.py = Python truy xuất dữ liệu gia phả. Đuôi file chỉ cho biết định dạng; phải đọc nội dung để biết đã có chức năng hay chỉ TODO. Danh mục mọi file và đầu mối: structure-inventory.md và file-ownership.md.
