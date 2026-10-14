"""Xây lại chỉ mục tìm kiếm AI

TRẠNG THÁI: KHUNG, CHƯA TRIỂN KHAI.
- Đọc HERITAGE_ITEMS và HERITAGE_MEDIA được cho phép; bản đầu chỉ xử lý văn bản nhập sẵn.
- Chia đoạn và tạo embedding vào AI_DOCUMENT_CHUNKS; lưu model/revision.
- Không tự quét ảnh/PDF chưa có bộ trích xuất; không gửi dữ liệu toàn hệ thống cho LLM.

Đối chiếu docs/api-documentation.md và docs/database-design.md.
Không trả dữ liệu giả như kết quả nghiệp vụ thật.
"""
