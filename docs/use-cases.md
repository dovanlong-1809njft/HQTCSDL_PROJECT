# Ca sử dụng trọng tâm v2

UC01 Đăng nhập: nhập tài khoản → API xác minh hash/trạng thái → tạo phiên/JWT → giao diện. Đăng xuất thu hồi phiên; token cũ bị từ chối.
UC02 Thêm người: Family Admin chọn gia đình/nhánh, nhập người và cha mẹ → API kiểm quyền → thủ tục kiểm quan hệ và thêm trong transaction → lỗi rollback, thành công hiển thị cây.
UC03 Duyệt thành viên: người xin tham gia ở pending → admin duyệt → một lần chuyển trạng thái và audit; hai phiên không duyệt trùng.
UC04 Cộng đồng: thành viên đăng bài/ảnh → lưu bài và gắn media theo quyền → bình luận/phản ứng; sửa/xóa theo chủ sở hữu hoặc quản trị.
UC05 RSVP: PUT /api/v1/families/{family_id}/events/{event_id}/rsvp → kiểm sự kiện/quyền/chỗ → giao tác cập nhật → không tạo bản ghi trùng.
UC06 Di sản: admin nhập tư liệu/câu chuyện/người tiêu biểu, gắn tệp → hiển thị đúng loại → cập nhật chỉ mục tìm kiếm.
UC07 AI: POST /api/v1/families/{family_id}/ai/ask → lọc quyền → lấy nguồn/quan hệ → LLM diễn giải → trả nguồn; không đủ dữ liệu thì báo rõ.
UC08 Báo cáo: chọn thời gian và loại → API lấy SQL thống kê → biểu đồ hoặc CSV có cùng số liệu.
UC09 Nhắc lịch: worker lấy sự kiện sắp diễn ra → tạo thông báo không trùng → người nhận xem/đánh dấu đã đọc.
UC10 Quản trị: System Admin khóa tài khoản/kiểm duyệt/cấu hình → lưu audit → kiểm tra quyền và token bị khóa.
UC11 Sao lưu/khôi phục: DBA thực hiện ngoài UI theo backup-restore.md; restore vào DB thử và kiểm dữ liệu.

Danh sách đầy đủ tiêu chí theo FR01–FR24 trong requirements.md. Đây là đặc tả mục tiêu, chưa phải bằng chứng tính năng đã có.
