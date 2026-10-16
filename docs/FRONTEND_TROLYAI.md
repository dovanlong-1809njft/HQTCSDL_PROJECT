# Trợ lý AI — frontend bước 8

## Cập nhật và chạy

Gói ZIP gồm toàn bộ frontend hiện tại cùng các hướng dẫn. Sao lưu/commit và đối chiếu phần nhóm tự sửa trước khi chép đè. Chép `frontend` và `docs` vào gốc `HQTCSDL_PROJECT`, thay thế file cùng đường dẫn.

```powershell
py -m http.server 5500 --directory frontend
```

Mở http://localhost:5500/pages/ai-assistant.html và nhấn Ctrl+F5. Dùng cùng địa chỉ/port với các trang đã làm để đọc cùng dữ liệu mẫu.

## Phạm vi của bước này

Đây là **giao diện trợ lý với xử lý mô phỏng cục bộ bằng JavaScript**. Chưa có LLM, API AI, embeddings, tìm kiếm ngữ nghĩa, OCR, nhận diện ảnh, dịch/phiên âm Hán Nôm hoặc kết nối Internet. Backend/database chưa thay đổi. Không cần API key và không gửi câu hỏi/tệp đến máy chủ.

Banner và các công cụ ghi rõ giới hạn. Không dùng câu trả lời mẫu để khẳng định thông tin chưa có trong dữ liệu.

## Đã triển khai

- Bố cục theo ảnh tham khảo: banner, chủ đề gợi ý, lịch sử bên trái; hội thoại ở giữa; công cụ, ví dụ và mẹo bên phải.
- Gửi câu hỏi bằng nút Gửi hoặc Enter, Shift+Enter xuống dòng; tối đa 2.000 ký tự/câu hỏi. Chọn gợi ý sẽ điền câu hỏi để người dùng kiểm tra trước khi gửi; công cụ thống kê chạy trực tiếp bằng nút.
- Lịch sử riêng cho từng gia đình: tạo cuộc mới, mở lại, tìm theo tiêu đề, đổi tên, xóa từng cuộc hoặc toàn bộ với xác nhận. Tối đa 20 cuộc, 50 lượt hỏi/đáp mỗi cuộc. Tải lại giữ lịch sử, mặc định hiển thị màn hình chào để người dùng chọn cuộc muốn mở.
- Nút sao chép câu trả lời (nếu trình duyệt chặn clipboard, mở ô chọn văn bản để Ctrl+C), đánh dấu hữu ích/cần cải thiện, tải hội thoại `.txt` UTF-8. Đánh giá chỉ lưu cục bộ, không huấn luyện hay gửi phản hồi cho dịch vụ AI.
- Nguồn dưới câu trả lời: mở hồ sơ gia đình, thành viên, tư liệu, sự kiện đang có; nguồn không còn sẽ báo rõ. Nguồn hiển thị dữ liệu hiện tại, còn câu trả lời là nội dung được tạo tại thời điểm hỏi.

### Các xử lý mô phỏng

- Giới thiệu gia đình lấy tên, mô tả, đại diện, số thành viên/chi nhánh từ FamilyStore. Không dựng thêm lịch sử hoặc nguồn gốc dòng họ.
- Thống kê đếm thành viên theo thế hệ, giới tính đã nhập, số quan hệ, tư liệu/sự kiện đã khởi tạo. Giới tính chưa nhập được tính riêng, không suy đoán từ họ tên. Số tư liệu/sự kiện chi tiết có thể bằng 0 nếu chưa mở/khởi tạo các module tương ứng.
- Tra cứu quan hệ bằng công cụ chọn hai người (kèm thế hệ/mã hồ sơ để phân biệt tên trùng). Tìm đường theo các cạnh cha mẹ–con/hôn nhân đang có; diễn giải từng cạnh, không tự kết luận cách xưng hô/huyết thống. Không có đường thì báo thiếu liên kết, không kết luận hai người không liên quan.
- Tìm theo từ khóa trong hồ sơ thành viên, nội dung tư liệu, sự kiện; tối đa 5 kết quả. Đây là tìm chuỗi/khớp từ đơn giản, không phải tìm kiếm ngữ nghĩa. Không đọc bài cộng đồng trong chức năng này.
- “Tóm tắt” là trích tối đa 3 câu đầu (mỗi câu hiển thị tối đa 600 ký tự) từ văn bản được chọn/dán hoặc TXT; không sinh bản diễn giải bằng AI. Đọc lại toàn văn để đối chiếu. Khi vừa dán văn bản vừa chọn tư liệu, văn bản dán được ưu tiên và không gắn nguồn tư liệu gây hiểu nhầm.
- Soạn bản nháp chúc sinh nhật, lời mời họp mặt, bài kỷ niệm theo mẫu. Những chi tiết chưa biết để trong `[ngoặc]`, không tự bịa ngày/địa điểm. Không tự đăng lên Cộng đồng hoặc gửi lời mời.
- Gợi ý sự kiện là khung việc cần chuẩn bị theo mẫu, có thể lấy tên/thời gian/địa điểm từ sự kiện đang có. Không tự tạo sự kiện hoặc nhắc việc.
- Nút Phân tích ảnh/Dịch & phiên âm mở thông tin “chưa kết nối”, không đưa ra kết quả giả. Hỏi trực tiếp nhận diện người/chữ trong ảnh cũng báo giới hạn.

## Tệp đính kèm

Tối đa 2 tệp/câu hỏi:

- TXT UTF-8 tối đa 1 MB. Chỉ giữ tối đa 10.000 ký tự đầu, có thông báo khi bị cắt. Tệp được đọc như văn bản, không thực thi HTML. Khi yêu cầu trích ý từ nhiều TXT, dùng tệp TXT đầu tiên.
- JPG/PNG tối đa 5 MB, được nén thành ảnh thu nhỏ JPEG cạnh dài tối đa 360px để xem lại; ảnh có thể mất độ trong suốt/chất lượng, không giữ ảnh gốc.
- Không đọc nội dung PDF/DOCX ở trang trợ lý. Các tệp này vẫn có thể lưu tại Di sản & tư liệu, nhưng phải bổ sung nội dung văn bản ở tư liệu hoặc dán/TXT để công cụ trích ý dùng được.
- Hội thoại lưu tên tệp, đoạn TXT/ảnh thu nhỏ. Không gửi lên máy chủ. Xuất hội thoại TXT chỉ liệt kê tên tệp, không nhúng ảnh hoặc xuất lại tệp gốc.
- Tệp đang đọc bị hủy nếu chuyển gia đình/cuộc trò chuyện. Bản nháp câu hỏi/tệp chưa gửi không lưu qua tải lại. Không thể gửi khi đang đọc tệp.

## Dữ liệu và giới hạn

Thêm `aiData: {version: 1, chats: [...]}` vào mỗi gia đình trong FamilyStore, giữ nguyên khóa dữ liệu cũ. Mỗi cuộc có tiêu đề, thời gian và mảng tin nhắn (vai trò, văn bản, nguồn, đính kèm, đánh giá).

Lưu trong localStorage theo trình duyệt/origin. Khi hết dung lượng hoặc bị chặn, giao diện báo chỉ giữ tạm trong RAM; phần chưa lưu sẽ mất sau tải lại. Chưa có hợp nhất khi sửa nhiều tab hoặc đồng bộ thiết bị. Khôi phục dữ liệu gia đình mẫu sẽ xóa cả lịch sử trợ lý của gia đình đó.

Trang chỉ đọc dữ liệu nghiệp vụ để trả lời, không tạo/sửa thành viên, bài viết, tư liệu hoặc sự kiện. Bản nháp văn bản vẫn cần người dùng sửa và tự chuyển sang trang chức năng khi muốn sử dụng.

## File chính

- `frontend/pages/ai-assistant.html`: bố cục và biểu mẫu (HTML).
- `frontend/assets/css/ai.css`: định dạng desktop/mobile (CSS).
- `frontend/assets/js/modules/ai.js`: hội thoại, công cụ mô phỏng, tệp và lịch sử (JavaScript).

Để tích hợp AI thật ở bước sau, tách phần tạo câu trả lời sang backend, thêm cơ chế truy xuất nguồn và xác thực/phân quyền. Không đặt khóa API trong JavaScript frontend.

## Kiểm tra

Đã kiểm tra cú pháp, tài nguyên HTML/ID và mô phỏng DOM: thống kê không đoán giới tính, nguồn dữ liệu, đường quan hệ/thiếu liên kết, giới hạn công cụ ảnh/dịch, trích ý văn bản, đọc TXT bằng FileReader thực trong jsdom, chuỗi HTML không thực thi, từ chối PDF, mẫu nháp không tạo bài/sự kiện, sao chép dự phòng, đánh giá/xuất TXT, tạo/đổi tên/tìm/xóa lịch sử, lưu/tải lại, tách hai gia đình và báo hết dung lượng.

Chưa kiểm tra bố cục bằng trình duyệt thực tế, clipboard hệ điều hành, giải mã/nén ảnh thật, bàn phím IME/cảm ứng hoặc focus native dialog. Không có dịch vụ AI để kiểm thử chất lượng mô hình. Thử Chrome/Edge desktop và chiều rộng 390px: menu, chat, Enter/Shift+Enter, gửi TXT/ảnh thật, chuyển gia đình trong lúc đọc tệp, mở nguồn và tải lại lịch sử.
