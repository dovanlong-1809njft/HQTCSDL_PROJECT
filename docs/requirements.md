# Yêu cầu hệ thống 

Ràng buộc người dùng đã chốt: Python cho backend; SQL Server/T-SQL, SSMS 22; giao diện web dùng trên Android/iOS/Windows. PostgreSQL trong đề xuất gốc được thay bằng SQL Server theo yêu cầu hiện tại.

Không coi thu hẹp chức năng trong tài liệu v1 là đã được chấp thuận. Ma trận yêu cầu dưới đây giữ mọi nhóm chức năng đã nêu, chọn cách thực hiện đơn giản và kiểm chứng được.
Dòng "Quản lý" bị thiếu đối tượng trong đề bài tạm hiểu là quản lý người trong gia phả; ghi rõ đây là giả định.

| Mã | Yêu cầu | Module phụ trách | Tiêu chí nghiệm thu dự kiến |
|---|---|---|---|
| FR01 | Đăng ký/xác thực/JWT/đăng xuất | auth | Đăng nhập đúng, sai bị từ chối; token đăng xuất không dùng lại được |
| FR02 | RBAC và hồ sơ người dùng | users | Kiểm tra quyền ở backend; sửa hồ sơ mình |
| FR03 | Gia đình và xác minh thành viên | families | Tạo gia đình; pending không đọc được dữ liệu; admin duyệt/từ chối |
| FR04 | Quản lý nhánh | families | Tạo/sửa/xóa có kiểm tra tham chiếu; gắn người đúng gia đình |
| FR05 | Người và quan hệ cha/mẹ-con | genealogy | Thêm/sửa; cấm chu trình và khác gia đình |
| FR06 | Hôn nhân | genealogy | Tạo/cập nhật/kết thúc hôn nhân hợp lệ |
| FR07 | Cây tương tác và truy vấn quan hệ | genealogy | Phóng to/thu nhỏ/chọn người; truy vấn đường quan hệ có căn cứ |
| FR08 | Bài đăng và tin gia đình | community | Tạo/xem/sửa/xóa theo quyền |
| FR09 | Bình luận và phản ứng | community | Bình luận CRUD; một phản ứng hiện hành/người/bài |
| FR10 | Chia sẻ ảnh và tệp | media | Upload, gắn đối tượng, xem/tải có kiểm tra quyền |
| FR11 | Thông báo gia đình | notifications | Admin tạo thông báo; chỉ người nhận xem/đánh dấu |
| FR12 | Sự kiện và RSVP | events | Tạo/sửa/hủy; RSVP không trùng; xem người tham gia |
| FR13 | Album sự kiện | media | Gắn/xem/gỡ ảnh của sự kiện đúng gia đình |
| FR14 | Nhắc lịch | notifications | Tác vụ nền tạo thông báo trong ứng dụng đúng hạn, không trùng |
| FR15 | Danh bạ nghề nghiệp/học vấn | directory | Hồ sơ và lọc tên/nghề/địa điểm/thế hệ có mốc |
| FR16 | Tư liệu, câu chuyện, người tiêu biểu | heritage | Các loại nội dung dùng ItemType; liên kết FeaturedMemberID |
| FR17 | Thư viện ảnh/lưu trữ số | heritage | Liệt kê tư liệu/ảnh, tải xuống theo quyền |
| FR18 | Tìm kiếm ngữ nghĩa | ai | Embedding thật; truy vấn khác từ khóa vẫn tìm được nội dung liên quan trong bộ test |
| FR19 | Hỏi đáp và giải thích quan hệ AI | ai | LLM trả lời có nguồn; quan hệ tính từ SQL/Python; thiếu dữ liệu báo rõ |
| FR20 | Tóm tắt AI | ai | Tóm tắt tư liệu được phép, không gọi tài nguyên ngoài gia đình |
| FR21 | Đề xuất thành viên và tư liệu | ai | Quan hệ/nhóm nghề cho người; tương đồng embedding cho tư liệu; ghi rõ phần luật/phần AI |
| FR22 | Thống kê/nhân khẩu học/báo cáo | dashboard | Thành viên, cộng đồng, sự kiện, độ tuổi/thế hệ; CSV khớp SQL |
| FR23 | Người dùng/kiểm duyệt/audit/cấu hình | admin | Chỉ System Admin; log hành động; khóa cấu hình cho phép |
| FR24 | Sao lưu và khôi phục | database | Có .bak trong môi trường demo và restore sang DB thử; không commit backup |

## Phi chức năng và giới hạn cần ghi đúng
| Mã | Nội dung | Cách xử lý / trạng thái |
|---|---|---|
| NF01 | Web responsive | Kiểm tra trang trên desktop và điện thoại thật; bảng/cây có điều khiển phù hợp |
| NF02 | Đa nền tảng | Một web/PWA trên Android/iOS/Windows. Nếu rubric yêu cầu APK/IPA/native thì đây còn là khoảng thiếu cần làm rõ |
| NF03 | Bảo mật JWT/RBAC | Băm Argon2; JWT có hạn; phiên thu hồi; kiểm tra quyền tài nguyên và tệp |
| NF04 | REST và mô-đun | Một backend FastAPI chia router/schema/service/repository; không tách microservice |
| NF05 | SQL Server/T-SQL | DDL/DML, thủ tục, giao tác và minh chứng đồng thời trên SSMS |
| NF06 | AI thật | Có embedding và LLM cho buổi nghiệm thu các chức năng AI; fallback ghi đúng là tra cứu thường |
| NF07 | Docker | Bắt buộc có build/run thực tế, cấu hình chưa triển khai ở bộ khung |
| NF08 | Tính khả dụng cao | Chưa đáp ứng HA thực tế. Healthcheck/restart/backup chỉ là vận hành cơ bản. Nếu bắt buộc HA: cần nhiều instance/backend, cân bằng tải và giải pháp dự phòng CSDL được thử failover; kế hoạch 21 ngày phải điều chỉnh |
| NF09 | Audit | Ghi người/thời điểm/hành động; chỉ vai trò phù hợp được xem |
| NF10 | Kiểm thử/hiệu năng | Tập demo đề xuất 100 người, 200 bài, 20 sự kiện, 50 tư liệu; đo thời gian trên máy nhóm, báo số đo thực; chưa có ngưỡng rubric |

Thông báo/nhắc lịch bản cơ bản nằm trong ứng dụng. Email/SMS/push ngoài ứng dụng không tự coi là bắt buộc khi đề chưa nói rõ. Học vấn/nghề nghiệp dùng hồ sơ văn bản hiện tại; chưa làm lịch sử nhiều công việc/trường học.

Mục tiêu là bản trình diễn tích hợp, không cam kết chất lượng sản phẩm vận hành quy mô lớn. Mọi hàng chỉ đánh dấu hoàn thành sau khi demo/test thật; không dùng số lượng file làm tỷ lệ hoàn thành.
