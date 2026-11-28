# Chương: Phân hệ Cộng đồng & Sự kiện

Người thực hiện: Nguyễn Duy Long (TV3) — Lập trình viên Tương tác, phân hệ Cộng đồng & Sự kiện.

Chương này dùng cho báo cáo nhóm. Phần cuối là outline slide và kịch bản demo.

Tài liệu chi tiết: [đặc tả yêu cầu](../requirements/community-events.md), [đặc tả API](../api-spec/community-events.md), [hướng dẫn sử dụng](../user-guide/community-events.md), [triển khai và thông báo đẩy](../deployment/mobile-push.md).

## 1. Phạm vi phụ trách

Phân hệ gồm hai nhóm chức năng:

- **Cộng đồng:** bảng tin của gia đình, bài viết kèm ảnh, bình luận, cảm xúc, báo cáo nội dung vi phạm.
- **Sự kiện:** sự kiện của gia đình, lịch theo tháng, trả lời tham gia, thư viện ảnh, nhắc nhở và thông báo đẩy ra điện thoại.

Toàn bộ nghiệp vụ đặt ở tầng cơ sở dữ liệu. Tầng API chỉ kiểm tra JWT rồi gọi thủ tục, không viết logic nghiệp vụ. Cách này giữ đúng yêu cầu môn học và bảo đảm nghiệp vụ không bị bỏ qua khi có thêm một client khác, ở đây là app Flutter gọi cùng bộ API với web.

## 2. Các đối tượng cơ sở dữ liệu đã xây dựng

| Loại | Tên | Vai trò |
| --- | --- | --- |
| View | `community.vw_NewsfeedPosts` | Một dòng là một bài viết kèm tác giả, số bình luận, số cảm xúc và danh sách ảnh ghép bằng `STRING_AGG ... WITHIN GROUP (ORDER BY ...)` |
| Function | `community.fn_GetMonthlyEvents` | Hàm trả bảng, lấy sự kiện trong một tháng kèm số người nhận tham gia |
| Procedure | `community.usp_CreatePostWithMedia` | Tạo bài viết và nhiều ảnh trong một giao tác, tách JSON bằng `OPENJSON` |
| Procedure | `community.usp_UpsertReaction` | Mỗi người một cảm xúc trên mỗi bài, dùng `MERGE ... WITH (HOLDLOCK)` |
| Procedure | `community.usp_UpsertEventRsvp` | Thêm hoặc cập nhật câu trả lời tham gia, cùng cơ chế `MERGE` |
| Procedure | `community.usp_ClaimDueReminders` | Lấy nhắc nhở đến hạn và đánh dấu đã gửi trong một câu lệnh, dùng `UPDLOCK, READPAST, ROWLOCK` |
| Procedure | `community.usp_ClaimUnpushedNotifications` | Lấy thông báo chưa đẩy kèm token thiết bị, cùng cơ chế claim |
| Trigger | `community.trg_ReportedContents_Escalation` | Đủ 3 báo cáo chờ xử lý thì ghi một dòng nhật ký để quản trị viên xem xét |

Tầng ứng dụng: 26 endpoint trong `apps/backend/app/domains/community` và `events`, hai endpoint đăng ký thiết bị trong `notifications/devices.py`, tiến trình nền trong `apps/worker`.

## 3. Những vấn đề đồng thời và cách xử lý

Đây là phần liên hệ trực tiếp với nội dung môn học. Mỗi tình huống dưới đây là một vấn đề truy xuất đồng thời có thật trong phân hệ, không phải ví dụ giả định.

### 3.1 Mất dữ liệu cập nhật khi hai phiên cùng đổi cảm xúc

Người dùng bấm hai lần liên tiếp, hoặc mở app trên hai máy. Nếu viết theo lối kiểm tra rồi chèn (`IF NOT EXISTS ... INSERT ... ELSE UPDATE`), hai phiên cùng đọc thấy chưa có cảm xúc, cùng chèn, và dòng thứ hai vi phạm `UQ_Reactions_Post_User`; nếu bảng không có ràng buộc này thì sinh ra hai dòng cảm xúc cho cùng một người.

Cách xử lý: một câu `MERGE ... WITH (HOLDLOCK)`. Gợi ý `HOLDLOCK` tương đương mức cô lập `SERIALIZABLE` cho câu lệnh đó, giữ khóa khoảng khóa nên phiên thứ hai phải chờ phiên thứ nhất kết thúc rồi mới quyết định chèn hay cập nhật. Kết quả cuối cùng luôn đúng một dòng, với loại cảm xúc của phiên ghi sau.

Kiểm chứng: `tests/database/tv3.integration.sql`, chế độ `TAB_A` và `TAB_B`, bước B3 và B4. Phiên B bị chờ hơn một giây và kết thúc với đúng một dòng.

### 3.2 Gửi trùng thông báo khi nhiều tiến trình nền cùng quét

Tiến trình nền quét nhắc nhở đến hạn. Nếu chạy hai bản, cả hai cùng đọc danh sách `pending` rồi cùng gửi, người dùng nhận thông báo hai lần.

Cách xử lý: `usp_ClaimDueReminders` dùng `UPDATE ... OUTPUT` trên một CTE có `WITH (UPDLOCK, READPAST, ROWLOCK)`:

- `UPDLOCK` giữ khóa cập nhật ngay khi đọc, nên không có hai phiên cùng nhận một dòng.
- `READPAST` cho phiên sau bỏ qua các dòng đang bị giữ thay vì chờ, nên hai tiến trình chia nhau công việc và không chặn nhau.
- `UPDATE ... OUTPUT` gộp việc lấy và đánh dấu vào một câu lệnh, không có khoảng hở giữa đọc và ghi.

Kiểm chứng: cùng tệp kiểm thử, bước B1 và B2. Phiên B không bị chờ, và lấy được dòng còn lại chứ không lấy dòng phiên A đang giữ. Cơ chế này dùng lại nguyên vẹn cho `usp_ClaimUnpushedNotifications` khi đẩy thông báo ra điện thoại.

### 3.3 Trạng thái nửa vời khi tạo bài viết kèm ảnh

Tạo bài rồi chèn ảnh là hai lệnh. Nếu lỗi ở lệnh thứ hai mà không có giao tác, bảng tin còn lại một bài viết thiếu ảnh và không có cách nào biết ảnh đã mất.

Cách xử lý: `usp_CreatePostWithMedia` kiểm tra đầu vào trước, sau đó mở `BEGIN TRAN`, bật `XACT_ABORT ON`, và bọc trong `TRY ... CATCH` có `ROLLBACK`. Hai lệnh chèn cùng thành công hoặc cùng bị hủy, đúng tính nguyên tố của giao tác.

Kiểm chứng: bước 2 trong chế độ `TEST`, gửi JSON sai định dạng và kiểm tra không có bài viết nào còn lại.

### 3.4 Leo thang lặp và chạy theo lô

Trigger ghi nhật ký khi nội dung đủ 3 báo cáo. Nếu viết đơn giản là đếm rồi ghi, thì báo cáo thứ tư, thứ năm cũng ghi thêm, nhật ký bị trùng. Ngoài ra trigger trong SQL Server chạy một lần cho cả lô, nên khi ba báo cáo vào cùng một lệnh `INSERT`, bảng `inserted` có ba dòng.

Cách xử lý: trigger so sánh tổng số báo cáo hiện tại với số báo cáo vừa chèn, chỉ ghi khi lô này đúng là lô làm vượt ngưỡng:

```sql
WHERE c.[Total] >= @Threshold
  AND c.[Total] - c.[NewOnes] < @Threshold;
```

Kiểm chứng: bước 6a đến 6d. Hai báo cáo chưa ghi gì, báo cáo thứ ba ghi một dòng, báo cáo thứ tư không ghi thêm, và ba báo cáo trong cùng một `INSERT` cũng chỉ ghi một dòng.

### 3.5 Kiểm soát truy cập ngay trong giao tác

Việc kiểm tra quyền dùng `heritage.usp_AssertFamilyAccess`, gọi bên trong giao tác và đọc `core.Users`, `genealogy.Members` với `HOLDLOCK`. Nhờ vậy quyền không thể bị thay đổi giữa lúc kiểm tra và lúc ghi dữ liệu.

Kiểm chứng: bước 7a, 7b, 7c. Thành viên chưa có hồ sơ gia phả bị từ chối, sau khi được liên kết thì ghi được, tài khoản không tồn tại bị chặn từ đầu.

## 4. Kiểm thử

| Tệp | Nội dung |
| --- | --- |
| `tests/database/tv3.integration.sql` | 20 khẳng định PASS/FAIL cho view, function, thủ tục, trigger và phân quyền, cộng 4 khẳng định cho hai kịch bản đồng thời chạy ở hai phiên |
| `tests/database/test_community_smoke.sql` | Chạy thử nhanh, mọi thứ trong một giao tác rồi `ROLLBACK` |
| `tests/api/test_community_events_api.py` | Kiểm thử tầng API |

Bộ tích hợp chạy theo chế độ: `TEST` tự tạo dữ liệu rồi dọn sạch; `SETUP` tạo dữ liệu cố định cho hai kịch bản đồng thời; `TAB_A` và `TAB_B` chạy ở hai cửa sổ truy vấn để quan sát việc chờ khóa; `CLEANUP` xóa dữ liệu test. Mọi dòng dữ liệu test đều mang dấu hiệu `TV3-ITEST` nên không lẫn với dữ liệu thật.

Phần quét nhắc nhở trong chế độ `TEST` được bọc trong một giao tác riêng và `ROLLBACK`, vì thủ tục quét toàn bảng `EventReminders` và nếu không bọc sẽ làm đổi trạng thái nhắc nhở của gia đình khác.

## 5. Kết quả và hạn chế

Đã làm được:

- Bảng tin, bình luận, cảm xúc, báo cáo vi phạm, sự kiện, lịch tháng, trả lời tham gia, thư viện ảnh, nhắc nhở, thông báo trong app, và đẩy thông báo ra điện thoại Android.
- Xử lý đúng bốn tình huống đồng thời nêu ở mục 3, có kiểm thử hai phiên chứng minh.
- Web và app Flutter dùng chung một bộ API.

Hạn chế và hướng phát triển:

- Ngưỡng leo thang báo cáo đang cố định trong trigger, nên chuyển vào `core.SystemConfigs` để quản trị viên đổi được.
- `usp_ClaimDueReminders` quét toàn bảng, chưa lọc theo gia đình. Dữ liệu lớn thì nên thêm tham số lọc.
- Nhắc nhở chuyển trực tiếp sang `sent` khi được lấy, chưa có trạng thái trung gian để phân biệt đang gửi và đã gửi.
- Thông báo đẩy trên iOS cần tài khoản Apple Developer trả phí và máy Mac, nên bản này chỉ làm cho Android.
- Muốn app dùng được khi máy cá nhân đã tắt thì phải đưa backend, database và tiến trình nền lên dịch vụ cloud; phương án và các điểm cần sửa đã ghi trong `docs/deployment/mobile-push.md`.

## 6. Outline slide

Bảy slide, khoảng năm phút.

1. **Phạm vi phụ trách.** Hai nhóm chức năng, vị trí trong kiến trúc chung. Một hình kiến trúc.
2. **Đối tượng cơ sở dữ liệu.** Bảng 8 đối tượng ở mục 2, tô đậm cột vai trò.
3. **Bài viết kèm ảnh là một giao tác.** Sơ đồ các bước trong `usp_CreatePostWithMedia`, nhấn `OPENJSON` và `ROLLBACK`.
4. **Không để trùng cảm xúc và trả lời tham gia.** Hình hai phiên song song, giải thích `MERGE ... WITH (HOLDLOCK)`.
5. **Không gửi trùng thông báo.** Hình hai tiến trình nền, giải thích `UPDLOCK, READPAST` và `UPDATE ... OUTPUT`.
6. **Trigger leo thang báo cáo.** Mốc 3 báo cáo, nhấn chuyện chạy theo lô và không ghi lặp.
7. **Kết quả kiểm thử.** Ảnh chụp bảng PASS của chế độ `TEST`, và ảnh hai cửa sổ `TAB_A`, `TAB_B`.

## 7. Kịch bản demo

Chuẩn bị trước: SQL Server đang chạy, backend ở cổng 8000, web ở cổng 5173, một cửa sổ SSMS mở sẵn tệp kiểm thử, một tài khoản `admin` và một tài khoản thành viên.

| Bước | Thao tác | Điều cần nói |
| --- | --- | --- |
| 1 | Mở `/community`, đăng bài kèm hai ảnh | Bài và ảnh vào cùng một giao tác; view ghép danh sách ảnh theo thứ tự tải lên |
| 2 | Bình luận và đổi cảm xúc hai lần | Mỗi người một cảm xúc trên mỗi bài, đổi loại thì cập nhật chứ không thêm dòng |
| 3 | Báo cáo bài bằng ba tài khoản, mở nhật ký quản trị | Trigger ghi đúng một dòng ở lần thứ ba |
| 4 | Mở `/events`, tạo sự kiện, trả lời tham gia hai lần | Chỉ giữ câu trả lời mới nhất, số người tham dự chỉ đếm Tham gia |
| 5 | Đặt nhắc nhở trước hiện tại một phút, chờ worker | Tiến trình nền quét và gửi; trên điện thoại thì thông báo hiện khi app đang đóng |
| 6 | Chạy `tv3.integration.sql` chế độ `TEST` | Toàn bộ khẳng định PASS |
| 7 | Chạy `TAB_A` rồi `TAB_B` ở hai cửa sổ | Phiên B không bị chờ khi lấy nhắc nhở nhưng bị chờ khi đổi cảm xúc, và kết quả chỉ còn một dòng |

Câu hỏi thầy hay hỏi và chỗ trả lời: vì sao dùng `HOLDLOCK` thay vì chỉ dựa vào ràng buộc duy nhất (mục 3.1); `READPAST` có bỏ sót dữ liệu không (mục 3.2, dòng bị bỏ qua sẽ được lấy ở lượt quét sau); trigger chạy theo dòng hay theo lô (mục 3.4); nếu gửi thông báo thất bại thì sao (`usp_ReleaseNotificationPush` trả lại để lượt sau gửi lại).
