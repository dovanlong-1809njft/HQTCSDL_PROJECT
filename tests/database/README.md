# Kiểm thử database bằng T-SQL

Các bài kiểm thử sử dụng T-SQL trên SQL Server, chạy bằng SSMS. Bộ test task 3 không cần PowerShell, Bash hoặc Docker. Dùng tài khoản quản trị có quyền tạo database và `EXECUTE AS USER` cho bài kiểm tra phân quyền.

## Task 3: View, Procedure và Trigger của TV 1

Toàn bộ kiểm thử task 3 nằm trong **[task3.integration.sql](task3.integration.sql)**. Mở file trong SSMS, đổi giá trị `@Mode` ở đầu file rồi Execute toàn bộ:

```sql
DECLARE @Mode VARCHAR(12) = 'SETUP';
```

| Giá trị @Mode | Chức năng                                                         |
| ------------- | ----------------------------------------------------------------- |
| SETUP         | Tạo database thử riêng `FamilyConnect_Task3Test`.                 |
| TEST          | Chạy kiểm thử View, Procedure, Trigger, quyền, audit và rollback. |
| TAB_A         | Duyệt yêu cầu thứ nhất, giữ transaction 10 giây.                  |
| TAB_B         | Duyệt yêu cầu cạnh tranh và kiểm tra kết quả hai phiên.           |
| CLEANUP       | Xóa database thử.                                                 |

1. Chạy file với `@Mode = 'SETUP'`. Script không ghi vào FamilyConnect.
2. Nạp lần lượt tất cả file `.sql` trong `database/schema/`, theo thứ tự tên file, vào database thử. Không nạp `seed/` hoặc `shared/06_permissions.sql`.
3. Nạp `database/views/01_core_views.sql`, `database/procedures/01_core_procs.sql` và `database/triggers/01_core_triggers.sql`, theo thứ tự, vào database thử.
4. Đổi `@Mode = 'TEST'`, Execute toàn bộ file và kiểm tra dòng `PASS` trong Messages.
5. Sao chép nội dung **cùng file** sang hai tab query SSMS, chọn `TAB_A` ở tab thứ nhất và `TAB_B` ở tab thứ hai. Chạy A trước rồi chạy B trong thời gian A chờ 10 giây. Kết quả phải có đúng một yêu cầu `approved`, một yêu cầu `rejected` và hồ sơ liên kết đúng tài khoản được duyệt.
6. Khi kiểm tra xong, đổi `@Mode = 'CLEANUP'` và Execute toàn bộ file.

Các file nguồn hiện dùng `$(DB_NAME)` để chọn database. Khi nạp ở bước 2–3, bật **Query → SQLCMD Mode** trong từng tab và thêm dòng sau ở đầu truy vấn, trước nội dung file:

```sql
:setvar DB_NAME "FamilyConnect_Task3Test"
```

SQLCMD chỉ thay tên database trước khi SQL Server thực thi; toàn bộ câu lệnh tạo bảng, ràng buộc, View, Procedure, Trigger và kiểm thử vẫn là T-SQL. Nếu muốn dùng chế độ SSMS thông thường, thay mọi `$(DB_NAME)` bằng `FamilyConnect_Task3Test` trong **bản truy vấn đang mở**, giữ nguyên file nguồn. File kiểm thử không cần SQLCMD Mode.

Mỗi lần kiểm thử dùng một database thử mới. Nếu test lỗi hoặc muốn chạy lại, chạy chế độ `CLEANUP` rồi thực hiện lại từ bước 1. Chế độ kiểm tra đồng thời cũng chạy một lần cho mỗi bộ dữ liệu thử. Nếu truy vấn bị dừng khi `NOEXEC` đang bật, mở tab mới hoặc chạy riêng `SET NOEXEC OFF;` trước khi bắt đầu lại.

Bộ test kiểm tra danh sách chờ xác minh, quyền theo vai trò/chi, tài khoản bị khóa, liên kết trùng, tự từ chối yêu cầu cạnh tranh, giữ nội dung khi bác báo cáo, xóa bài/bình luận/ảnh khi xử lý vi phạm, audit, cập nhật nhiều dòng và rollback khi ghi audit thất bại. Các bài gây lỗi rollback chạy trên database thử riêng; không bọc toàn bộ file bằng một transaction ngoài.

## Kiểm thử TV 3: Cộng đồng & Sự kiện

Toàn bộ kiểm thử phân hệ Cộng đồng & Sự kiện nằm trong **[tv3.integration.sql](tv3.integration.sql)**. File chạy trên database `FamilyConnect` đã nạp đầy đủ `schema/`, `views/`, `procedures/` và `triggers/`, không cần tạo database thử riêng. Mở file trong SSMS, đổi `@Mode` ở đầu file rồi Execute toàn bộ:

```sql
DECLARE @Mode VARCHAR(10) = 'TEST';
```

| Giá trị @Mode | Chức năng                                                                        |
| ------------- | -------------------------------------------------------------------------------- |
| TEST          | 20 khẳng định cho View, Function, Procedure, Trigger và phân quyền. Tự tạo dữ liệu và tự dọn sạch. |
| SETUP         | Tạo dữ liệu cố định cho hai kịch bản đồng thời.                                  |
| TAB_A         | Phiên thứ nhất: lấy một nhắc nhở và thả cảm xúc, giữ transaction 10 giây.         |
| TAB_B         | Phiên thứ hai: chạy trong 10 giây đó, kiểm tra việc chờ khóa và không gửi trùng.  |
| CLEANUP       | Xóa dữ liệu do SETUP, TAB_A và TAB_B để lại.                                     |

1. Chạy `@Mode = 'TEST'` và đọc cột `KetQua`; tất cả phải là `PASS`. Cột `ChiTiet` ghi giá trị thực tế và giá trị kỳ vọng của từng bước.
2. Chạy `@Mode = 'SETUP'`.
3. Sao chép nội dung **cùng file** sang hai tab query SSMS, chọn `TAB_A` ở tab thứ nhất và `TAB_B` ở tab thứ hai. Chạy A trước rồi chạy B ngay trong 10 giây A đang chờ. Kỳ vọng: B lấy nhắc nhở không bị chờ và không lấy lại dòng A đang giữ (`READPAST`), nhưng B phải chờ A commit khi đổi cảm xúc (`HOLDLOCK`), và cuối cùng chỉ còn đúng một dòng cảm xúc.
4. Chạy `@Mode = 'CLEANUP'`.

File dùng `$(DB_NAME)` nên cần bật **Query → SQLCMD Mode** và thêm `:setvar DB_NAME "FamilyConnect"` ở đầu truy vấn, hoặc chạy bằng `sqlcmd -v DB_NAME=FamilyConnect`.

Mọi dòng dữ liệu kiểm thử đều mang dấu hiệu `TV3-ITEST` để `CLEANUP` xóa đúng phạm vi. Chế độ `TEST` bọc phần quét nhắc nhở trong một transaction riêng rồi `ROLLBACK`, vì `usp_ClaimDueReminders` quét toàn bảng `EventReminders`; nhờ vậy trạng thái nhắc nhở của các gia đình khác không bị thay đổi. Chạy lại `TAB_A`, `TAB_B` thì nên `CLEANUP` rồi `SETUP` lại, vì nhắc nhở đã chuyển sang `sent`.

Ngoài ra [test_community_smoke.sql](test_community_smoke.sql) là bản chạy thử nhanh, mọi thứ trong một transaction rồi `ROLLBACK`.

## Kiểm thử AI hiện có

[test_05_ai_vector_ssms.sql](test_05_ai_vector_ssms.sql) kiểm tra hàm cosine và Procedure upsert chunk. File này dùng `FamilyConnect` và dữ liệu seed; không thuộc bộ test task 3.
