# Thư viện và công cụ dự kiến

Danh sách sau là đề xuất triển khai. requirements.txt giữ bốn thư viện nền có sẵn; chưa cố định phiên bản vì chưa chạy tích hợp. Người tích hợp cài/kiểm tra rồi ghi phiên bản tương thích vào requirements.txt; không tự nhận bản mới nhất luôn tương thích.

| Thành phần | Lựa chọn | Khi thêm |
|---|---|---|
| Backend | Python 3.11+, FastAPI, uvicorn[standard] | Đã có trong khung, cần cài trên máy |
| SQL | pyodbc + Microsoft ODBC Driver 18 | Driver hệ điều hành cài riêng |
| Cấu hình | python-dotenv | Nạp .env bằng đường dẫn gốc rõ ràng |
| Dữ liệu API | Pydantic | Khi viết schema; khai báo trực tiếp dependency nếu dùng trực tiếp |
| JWT | PyJWT | Module auth |
| Mật khẩu | pwdlib[argon2] | Module auth |
| Upload | python-multipart | Module media |
| API ngoài / test | httpx | LLM adapter và tests |
| Test | pytest | requirements-dev.txt |
| Embedding | sentence-transformers, numpy | requirements-ai.txt; tải model hỗ trợ tiếng Việt trước demo |
| Giao diện | Bootstrap 5 | Lưu bản phân phối cố định trong assets/vendor khi triển khai để giảm lệ thuộc CDN |
| Gia phả | vis-network | Sơ đồ tương tác; xử lý hôn nhân và thế hệ bằng dữ liệu của dự án |
| Thống kê | Chart.js | Dashboard |

Nhắc lịch có thể dùng một worker chạy vòng định kỳ đơn giản; không cần Redis/Celery cho demo. LLM: chọn một nhà cung cấp/model thực tế qua cấu hình, kiểm tra endpoint, chi phí và API key trước khi triển khai; bộ khung không giả định mọi API đều cùng chuẩn.

Nguồn để người triển khai kiểm tra phiên bản/cách dùng:
- https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- https://github.com/mkleehammer/pyodbc
- https://getbootstrap.com/docs/5.3/getting-started/introduction/
- https://visjs.github.io/vis-network/
- https://www.chartjs.org/docs/latest/
- https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html
