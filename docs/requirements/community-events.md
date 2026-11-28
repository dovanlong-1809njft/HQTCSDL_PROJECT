# Đặc tả yêu cầu — Cộng đồng & Sự kiện

Phân hệ do TV3 phụ trách. Tài liệu này là phần chi tiết của [đặc tả yêu cầu chung](README.md), mô tả yêu cầu nghiệp vụ của bảng tin, bình luận, cảm xúc, báo cáo vi phạm, sự kiện, RSVP và nhắc lịch.

Tài liệu liên quan:

- [Đặc tả API Cộng đồng & Sự kiện](../api-spec/community-events.md) — 26 endpoint.
- [Hướng dẫn sử dụng](../user-guide/community-events.md).
- Kiểm thử: [tests/database/tv3.integration.sql](../../tests/database/tv3.integration.sql), [tests/database/test_community_smoke.sql](../../tests/database/test_community_smoke.sql), [tests/api/test_community_events_api.py](../../tests/api/test_community_events_api.py).

Quy ước mã yêu cầu: `FR-CM-xx` cho cộng đồng, `FR-EV-xx` cho sự kiện, `NFR-xx` cho yêu cầu phi chức năng.

## 1. Vai trò liên quan

| Vai trò | Quyền trong phân hệ này |
| --- | --- |
| `member` | Xem bảng tin, đăng bài, bình luận, bày tỏ cảm xúc, RSVP, báo cáo vi phạm — chỉ trong gia đình mình có hồ sơ gia phả. |
| `family_head` | Như `member`, thêm quyền đăng bài thông báo (`IsAnnouncement = 1`) và quản lý sự kiện của gia đình. |
| `admin` | Toàn quyền trên mọi gia đình, xử lý nội dung bị báo cáo. |

Cơ chế kiểm tra quyền dùng chung với TV4: `heritage.usp_AssertFamilyAccess @ActorUserId, @FamilyId, @Manage`. Thủ tục báo lỗi `51403` khi tài khoản không hoạt động, không thuộc gia đình, hoặc không đủ quyền quản lý; báo `51404` khi gia đình không tồn tại.

## 2. Yêu cầu chức năng

### 2.1 Bảng tin và tương tác

| Mã | Yêu cầu | Ưu tiên | Đối tượng CSDL |
| --- | --- | --- | --- |
| FR-CM-01 | Thành viên xem được bảng tin của gia đình: mỗi bài kèm tên tác giả, nội dung, thời điểm đăng, số bình luận, số cảm xúc và danh sách ảnh. | Cao | `community.vw_NewsfeedPosts` |
| FR-CM-02 | Thành viên đăng bài kèm nhiều ảnh trong một lần gửi. Bài và toàn bộ ảnh phải cùng được lưu, hoặc không lưu gì. | Cao | `community.usp_CreatePostWithMedia` |
| FR-CM-03 | Thành viên bình luận, xem và xóa bình luận của mình. | Trung bình | `community.Comments` |
| FR-CM-04 | Mỗi người chỉ có một cảm xúc trên mỗi bài. Bày tỏ lần nữa với loại khác thì đổi loại, không tạo thêm dòng. Gỡ cảm xúc được. | Trung bình | `community.usp_UpsertReaction` |
| FR-CM-05 | Thành viên báo cáo bài, bình luận hoặc ảnh vi phạm. Khi một nội dung đạt 3 báo cáo đang chờ xử lý, hệ thống tự ghi một dòng nhật ký để quản trị viên xem xét, và chỉ ghi đúng một lần. | Cao | `community.trg_ReportedContents_Escalation` |

Quy tắc nghiệp vụ:

- BR-CM-01: Nội dung bài viết và bình luận không được rỗng (ràng buộc `CHECK` trên `Content`).
- BR-CM-02: Loại cảm xúc chỉ nhận `Like`, `Love`, `Haha`, `Wow`, `Sad`, `Angry`.
- BR-CM-03: `ReportedContents.TargetType` chỉ nhận `post`, `comment`, `photo`; vì `TargetId` là quan hệ đa hình nên tầng API phải kiểm tra mục tiêu tồn tại theo đúng loại.
- BR-CM-04: Ngưỡng leo thang là 3 báo cáo `pending`. Đổi ngưỡng thì sửa biến `@Threshold` trong trigger.
- BR-CM-05: Xóa bài thì ảnh, bình luận và cảm xúc của bài bị xóa theo (`ON DELETE CASCADE`).

### 2.2 Sự kiện, RSVP và nhắc lịch

| Mã | Yêu cầu | Ưu tiên | Đối tượng CSDL |
| --- | --- | --- | --- |
| FR-EV-01 | Tạo, sửa, xóa sự kiện của gia đình với tiêu đề, thời gian bắt đầu, thời gian kết thúc và địa điểm. | Cao | `community.Events` |
| FR-EV-02 | Xem lịch sự kiện theo tháng, kèm số người đã nhận tham gia. | Cao | `community.fn_GetMonthlyEvents` |
| FR-EV-03 | Thành viên trả lời tham gia (`Going`, `Maybe`, `Declined`). Trả lời lại thì cập nhật, không tạo dòng trùng. | Cao | `community.usp_UpsertEventRsvp` |
| FR-EV-04 | Tạo nhắc nhở cho sự kiện. Tiến trình nền quét định kỳ, lấy các nhắc nhở đã đến hạn và gửi thông báo. Mỗi nhắc nhở chỉ được gửi một lần, kể cả khi nhiều tiến trình chạy song song. | Cao | `community.usp_ClaimDueReminders` |
| FR-EV-05 | Lưu ảnh sự kiện vào thư viện của sự kiện. | Thấp | `community.EventGalleries` |

Quy tắc nghiệp vụ:

- BR-EV-01: Một thành viên chỉ có một bản ghi RSVP cho mỗi sự kiện (`UQ_EventParticipants_Event_Member`).
- BR-EV-02: `RsvpStatus` chỉ nhận `Pending`, `Going`, `Maybe`, `Declined`; `GoingCount` chỉ đếm `Going`.
- BR-EV-03: Trạng thái nhắc nhở chỉ nhận `pending`, `sent`, `failed`, `cancelled`. Lấy được coi là đã chuyển sang `sent`; nếu gửi thất bại, tiến trình nền cập nhật lại thành `failed`.
- BR-EV-04: Lịch tháng lấy theo nửa khoảng `[ngày 1 của tháng, ngày 1 của tháng sau)`, nên sự kiện lúc 23:59 ngày cuối tháng vẫn thuộc tháng đó.
- BR-EV-05: Xóa sự kiện thì RSVP, nhắc nhở và ảnh của sự kiện bị xóa theo.

### 2.3 Đặc tả chi tiết FR-CM-02 (mẫu cho các yêu cầu khác)

| Mục | Nội dung |
| --- | --- |
| Tác nhân | Thành viên đã đăng nhập |
| Điều kiện trước | JWT hợp lệ; tài khoản `IsActive = 1`; có hồ sơ gia phả thuộc gia đình đích, hoặc là `admin` |
| Đầu vào | `UserId`, `FamilyId`, `Content`, `MediaJson` dạng `[{"url":"...","type":"image"}]`, `IsAnnouncement` |
| Luồng chính | 1. Kiểm tra người dùng và gia đình tồn tại. 2. Kiểm tra `MediaJson` là JSON hợp lệ. 3. Mở giao tác. 4. Kiểm tra quyền truy cập gia đình. 5. Chèn bài, lấy `PostId` qua `OUTPUT`. 6. Tách `MediaJson` bằng `OPENJSON` và chèn vào `PostMedia`. 7. `COMMIT`, trả `PostId`. |
| Luồng thay thế | Người dùng không tồn tại → lỗi `50701`. Gia đình không tồn tại → `50702`. `MediaJson` sai định dạng → `50703`. Không đủ quyền → `51403`. Mọi lỗi trong giao tác đều `ROLLBACK` và không để lại bài viết nào. |
| Điều kiện sau | Bài viết và toàn bộ ảnh cùng tồn tại, hoặc không có gì được lưu. Bài mới xuất hiện ngay trên `vw_NewsfeedPosts`. |
| Kiểm thử | `tv3.integration.sql` bước 1a, 1b, 2, 7a, 7b, 7c |

## 3. Yêu cầu phi chức năng

| Mã | Yêu cầu | Cách kiểm chứng |
| --- | --- | --- |
| NFR-CM-01 | Thao tác tạo bài kèm ảnh là nguyên tử: không tồn tại trạng thái có bài mà thiếu ảnh, hoặc có ảnh mà không có bài. | `tv3.integration.sql` bước 2 |
| NFR-CM-02 | Hai phiên cùng bày tỏ cảm xúc trên một bài của cùng một người không tạo ra dòng trùng và không làm mất lần ghi nào. Dùng `MERGE ... WITH (HOLDLOCK)` để phiên sau chờ phiên trước rồi cập nhật. | `tv3.integration.sql` chế độ `TAB_A` / `TAB_B`, bước B3, B4 |
| NFR-EV-01 | Hai tiến trình nền quét nhắc nhở cùng lúc không gửi trùng và không chặn nhau. Dùng `UPDLOCK, READPAST, ROWLOCK` kèm `UPDATE ... OUTPUT` để lấy và đánh dấu trong một câu lệnh. | `tv3.integration.sql` bước B1, B2, 5a–5c |
| NFR-EV-02 | Quét nhắc nhở đến hạn dùng được chỉ mục `IX_EventReminders_Time_Status`, không quét toàn bảng. | Xem execution plan khi chạy `usp_ClaimDueReminders` |
| NFR-CM-03 | Mỗi lần leo thang nội dung bị báo cáo chỉ ghi một dòng nhật ký, kể cả khi nhiều báo cáo vào cùng một câu lệnh `INSERT`. | `tv3.integration.sql` bước 6a–6d |
| NFR-CM-04 | Mọi endpoint của phân hệ yêu cầu JWT và kiểm tra quyền theo gia đình trước khi đọc hoặc ghi. | `tests/api/test_community_events_api.py` |

## 4. Những điểm còn để mở

- Ngưỡng leo thang đang cố định trong trigger; nếu nhóm muốn cấu hình được thì nên chuyển sang `core.SystemConfigs`.
- `usp_ClaimDueReminders` quét toàn bộ bảng `EventReminders`, chưa lọc theo gia đình. Khi dữ liệu lớn, cân nhắc thêm tham số lọc hoặc phân vùng theo gia đình.
- Nhắc nhở đang chuyển trực tiếp sang `sent` khi được lấy. Nếu muốn phân biệt rõ "đang gửi" và "đã gửi", cần thêm trạng thái `processing` vào ràng buộc `CK_EventReminders_Status`.
