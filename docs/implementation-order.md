# Kế hoạch triển khai 21 ngày — bản thống nhất

Ngày là số thứ tự từ lúc nhóm bắt đầu. A–E là nhóm trách nhiệm, chưa phải năm người đã xác nhận. Có thể gộp/tách theo nhân lực thực tế. docs/file-ownership.md là nguồn phân công theo file.

| Ngày | Công việc | Điều kiện hoàn thành |
|---|---|---|
| 1–3 | A chốt ERD/từ điển dữ liệu; B hợp đồng API/quyền; C gia phả; D mẫu giao diện và upload; E AI/kiểm thử/vận hành | Tên bảng, trường, payload và mức nghiệm thu rõ; không còn hiểu khác nhau về PWA/HA |
| 4–7 | A script 01–07 theo luồng lõi; B kết nối/auth/family; C thêm người/cây; D giao diện chung; E dữ liệu demo, thiết lập AI | Đăng nhập → tạo gia đình → thêm người → xem cây dùng SQL Server thật; bắt đầu tích hợp hằng ngày |
| 8–11 | B duyệt/nhánh/quản trị; C hôn nhân/danh bạ/quan hệ; D bài/bình luận/ảnh/sự kiện; E di sản/dashboard | Mỗi module có ít nhất luồng đầy đủ qua UI/API/DB, quyền và xử lý lỗi |
| 12–14 | Hoàn thiện RSVP/album/nhắc lịch; E AI ngữ nghĩa/hỏi đáp/tóm tắt/đề xuất và báo cáo | Demo mọi hàng FR01–FR24; phần chưa đạt ghi cụ thể, không bỏ âm thầm |
| 15–18 | D PWA/thiết bị; E Docker và tích hợp; A backup/restore/giao tác/đồng thời; mọi nhóm test quyền/lỗi | Build/run trên máy thứ hai; minh chứng rollback, tranh chấp, khôi phục, AI và đa nền tảng |
| 19–21 | Sửa lỗi, hoàn thiện tài liệu, ảnh/video minh chứng, diễn tập | Source + hướng dẫn + dữ liệu demo + báo cáo; công khai khoảng thiếu |

Không chờ tới tuần 3 mới nối frontend/backend. Thủ tục và giao tác làm cùng nghiệp vụ ngay tuần 1–2; tuần 3 kiểm chứng, không viết toàn bộ từ đầu.
Docker và PWA có thời gian riêng, không còn là mục "nếu kịp". HA thực tế/app native nếu bị bắt buộc là phạm vi bổ sung có tác động tiến độ, không được dùng restart/PWA để tự nhận đáp ứng.

Định nghĩa hoàn thành: code có thật, dữ liệu SQL thật, đúng quyền, chạy trên máy thứ hai, test liên quan có kết quả, tài liệu cập nhật, người khác review. Khung TODO chưa hoàn thành.
