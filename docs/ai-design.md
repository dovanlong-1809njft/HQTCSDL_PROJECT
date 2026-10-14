# AI — thiết kế bản trình diễn

Mục tiêu: tìm kiếm ngữ nghĩa thật, hỏi đáp có nguồn, giải thích quan hệ, tóm tắt, đề xuất. Không huấn luyện mô hình riêng.

1. Bản đầu chỉ lập chỉ mục nội dung văn bản trong HERITAGE_ITEMS; file PDF/ảnh được lưu/tải nhưng chưa tự OCR. Khi cần nội dung của chúng, người nhập thêm mô tả/văn bản vào tư liệu.
2. embedding_client tải một model đa ngôn ngữ hỗ trợ tiếng Việt đã kiểm tra, cố định revision; scripts/rebuild_search_index.py chia đoạn và ghi AI_DOCUMENT_CHUNKS trong SQL Server.
3. search_service lọc FamilyID, trạng thái nguồn và quyền trước khi lấy vector; tính tương đồng bằng Python cho dữ liệu nhỏ. Không cần PostgreSQL/pgvector hay database thứ hai.
4. ai_service lấy top nguồn, gọi llm_client, trả nguồn tư liệu. Văn bản nguồn là dữ liệu, không được cho phép ghi đè chỉ thị kiểm soát quyền của hệ thống.
5. Quan hệ phả hệ được tính xác định từ PARENT_CHILD/MARRIAGES; LLM diễn giải đường quan hệ và không tự bịa người/quan hệ.
6. Tóm tắt nhận heritage_id, backend tự lấy dữ liệu có quyền. Đề xuất tư liệu dùng embedding; đề xuất người liên quan dùng quan hệ/nghề nghiệp với lý do, phân biệt rõ luật và AI.
7. Khi tắt AI/thiếu key: trả trạng thái không khả dụng; có thể cung cấp tra cứu thông thường nhưng ghi đúng tên. Thiếu key không được coi là đã nghiệm thu hỏi đáp/tóm tắt AI.

Kiểm thử: truy vấn đồng nghĩa tiếng Việt, nguồn không đủ, tư liệu bị ẩn/xóa, người gia đình khác, API timeout/429, model index khác dimension. Không tải dữ liệu thật để demo.
