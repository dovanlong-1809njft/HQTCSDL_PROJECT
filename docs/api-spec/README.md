# Đặc tả API

FastAPI tạo OpenAPI tại http://localhost:8000/docs.

Đã triển khai: GET /health, POST /api/auth/register, POST /api/auth/login và GET /api/auth/me (Bearer JWT).

ERD có 22 bảng. Danh bạ dùng Educations và WorkHistories; cộng đồng có PostMedia và ReportedContents; sự kiện có EventReminders và EventGalleries; di sản có Honors; cấu hình có SystemConfigs. SQL đã có các bảng này, nhưng API CRUD tương ứng chưa triển khai.

API mới phải kiểm tra JWT và quyền theo gia đình/chi nhánh. Members không còn Occupation. ReportedContents.TargetId là quan hệ đa hình cần xác thực theo TargetType. SystemConfigs không lưu bí mật.
