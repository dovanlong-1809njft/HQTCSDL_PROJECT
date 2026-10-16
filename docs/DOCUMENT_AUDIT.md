# Báo cáo rà soát tài liệu — 16/10/2026

## Phạm vi và nguyên tắc

- **Nguồn gốc:** `FamilyConnect_Frontend(3).zip` do chủ dự án cung cấp. So sánh tài liệu trong ZIP với tên file và các đoạn code đang có.
- **Chỉ thay đổi `.md` / `.txt`;** không sửa HTML, CSS, JS, Python, SQL, JSON, YAML hoặc ảnh.
- **Không xóa file:** thay vì vậy liệt kê trong `DOCUMENT_REVIEW_CANDIDATES.md`.
- **Không tự đoán ngày commit:** lịch sử `DEVELOPMENT_HISTORY.md` phân biệt ngày ghi trong tài liệu và mốc theo trò chuyện; chưa có `git log` để đối chiếu.

## Sai lệch tìm thấy và hướng xử lý

| Phát hiện | Ảnh hưởng | Tài liệu đã/đang xử lý |
|---|---|---|
| `structure-inventory.md` ghi 222 file trong ZIP gốc; sau khi thêm các tài liệu rà soát, bản bàn giao có **242 file** | Thành viên mới không thấy file V3–V5 | Tạo lại kiểm kê từ thư mục thực tế |
| `file-ownership.md` thiếu CSS/JS Sidebar, V3–V5 và một số file mới | Không rõ người chịu trách nhiệm | Đồng bộ đầu mối A–E; chỉ là gợi ý, chưa chỉ định con người |
| `README.md`, `frontend/README.md`, `SCAFFOLD_STATUS.md`, `deployment-guide.md`, `user-guide.md` còn mô tả nhiều trang là placeholder | Nhầm mức độ hoàn thành | Cập nhật mô tả thành “Frontend mẫu đã có code, nhưng chưa tích hợp Backend/SQL” |
| Trong ZIP gốc `index.html` chuyển trực tiếp `dashboard.html`, trái hướng dẫn V4 | Gây bước chuyển hướng thừa trước khi tới Đăng nhập | **Đã xử lý ở V7:** thay `frontend/index.html` để kiểm tra phiên dùng thử trước khi chuyển trang |
| Lịch trình 21 ngày được lập trước khi Frontend phát triển | Thành viên có thể coi ngày 1 như chưa có gì | Thêm mô tả giai đoạn Frontend đã có; giữ lịch như bản kế hoạch để nhóm hiệu chỉnh |
| Tài liệu V3/V4/V5 đang rời rạc | Khó biết giai đoạn nào thay đổi gì | Thêm nhật ký `DEVELOPMENT_HISTORY.md` và bản đồ docs |
| Có tài liệu đề xuất DB/AI/Docker khá đầy đủ nhưng code phần lớn là khung | Dễ quảng cáo quá mức khi nộp báo cáo | `PROJECT_STATUS.md`, `FRONTEND_FEATURE_MATRIX.md`, checklist với trạng thái rõ |

## Tệp không tự ý xử lý

- `docs/sw.js` có vẻ không đúng thư mục cho service worker; giữ nguyên và đề xuất kiểm tra sau.
- Các file `.gitkeep` không còn thiết yếu khi thư mục đã có file khác; vẫn giữ nguyên.
- Không thay đổi tên/đường dẫn của module đang được Frontend sử dụng.

## Checklist kiểm chứng của người nhận ZIP

- [ ] So sánh ZIP tài liệu này với bản gốc bằng `git diff -- '*.md' '*.txt'`.
- [ ] Xem README và trạng thái hiện tại có đúng trải nghiệm trên máy không.
- [ ] Đối chiếu tên file trong `structure-inventory.md` với Explorer.
- [ ] Xem lại các file trong `DOCUMENT_REVIEW_CANDIDATES.md` nhưng **chưa xóa**.
- [ ] Mở trình duyệt kiểm thử các trang cốt lõi; chưa thể coi mọi tính năng đã được kiểm tra E2E chỉ từ rà soát tài liệu.
- [ ] Đối chiếu `DEVELOPMENT_HISTORY.md` với GitHub PR/commit trước khi dùng làm lịch sử chính thức.

## Kết quả đối chiếu và đóng gói

- ZIP gốc: **237 file**.
- Sau khi thêm tài liệu: **242 file**.
- Chỉnh sửa nội dung: **16 file `.md`/`.txt`**.
- Bổ sung mới: **5 file `.md`**.
- Xóa file: **0**.
- File mã nguồn và tài nguyên không phải Markdown/TXT: **giữ nguyên byte-for-byte** so với ZIP gốc.
- Đường dẫn tại `structure-inventory.md` và `file-ownership.md` bao phủ đủ 242/242 file.
- Đã kiểm tra các liên kết Markdown nội bộ của tài liệu được cập nhật (chưa chạy kiểm thử web/API/SQL).

## Phụ lục kiểm tra V7 — lối vào web app

- Tài liệu này vốn mô tả **đợt chỉ sửa `.md`/`.txt` V6**; phần ghi nguyên tắc và kết quả V6 phía trên vẫn được bảo lưu để giữ lịch sử.
- **Đợt V7 theo yêu cầu mới:** sửa **1 file HTML duy nhất** là `frontend/index.html`, cập nhật những file Markdown/TXT đang ghi sai lệch cũ; **không xóa bất kỳ file nào**.
- Luồng mở `/` trong V7: chưa có phiên trình duyệt → Login; có phiên mẫu → Dashboard. Phải kiểm tra thật trên Cốc Cốc/Chrome.
- Phần kiểm kê cấu trúc **không đổi** vì V7 không tạo hoặc xóa đường dẫn file.
