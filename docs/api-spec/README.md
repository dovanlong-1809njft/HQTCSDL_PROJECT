# Đặc tả API

FastAPI tự tạo tài liệu OpenAPI. Khi backend đang chạy, có thể xem giao diện Swagger tại `http://localhost:8000/docs` hoặc xem nội dung JSON tại `http://localhost:8000/openapi.json`.

Hiện API xác thực gồm:

- `POST /api/auth/register`: tạo tài khoản và trả JWT.
- `POST /api/auth/login`: đăng nhập và trả JWT.
- `GET /api/auth/me`: đọc hồ sơ tài khoản hiện tại, cần header `Authorization: Bearer <access_token>`.

Hiện nhóm mới triển khai các API xác thực. Những API gia phả, cộng đồng, sự kiện và di sản sẽ được bổ sung khi các module tương ứng hoàn thành. ERD là thiết kế tham khảo; các file T-SQL trong `database/schema/` đang chờ nhóm bổ sung.
