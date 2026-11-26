# API Cộng đồng & Sự kiện

Đặc tả 26 endpoint của hai phân hệ `community` và `events` (Thành viên 3).

Mã nguồn: `apps/backend/app/domains/community/` và `apps/backend/app/domains/events/`.

## Quy ước chung

- Mọi endpoint đều có tiền tố `/api` và **bắt buộc JWT**: gửi header `Authorization: Bearer <token>`. Lấy token qua `POST /api/auth/login`.
- Thân yêu cầu và phản hồi đều là JSON. Mọi mã định danh là UUID.
- Thời gian gửi lên và trả về theo giờ UTC, định dạng ISO 8601 (`2026-11-30T18:30:00`).
- Schema yêu cầu đặt `extra="forbid"`: gửi thừa trường sẽ bị từ chối.

| Mã lỗi | Khi nào |
|---|---|
| `401` | Thiếu token hoặc token hết hạn |
| `403` | Không thuộc gia đình đó, hoặc không đủ quyền sửa/xóa |
| `404` | Không tìm thấy bài viết, sự kiện, bình luận |
| `422` | Dữ liệu gửi lên sai định dạng hoặc sai ràng buộc |

Endpoint phân trang nhận `page` (từ 1) và `page_size` (1–100), trả về:

```json
{ "items": [], "total": 0, "page": 1, "page_size": 20 }
```

---

# Phân hệ Cộng đồng — `/api/community`

## 1. Đăng bài kèm ảnh

`POST /api/community/posts` → **201**

Gọi thủ tục `community.usp_CreatePostWithMedia`. Bài viết và toàn bộ ảnh được ghi trong **một giao tác**; hỏng bất kỳ bước nào thì rollback cả hai, không để lại bài viết mất ảnh.

```json
{
  "family_id": "11111111-1111-1111-1111-111111111111",
  "content": "Ảnh họp mặt cuối tuần",
  "media": [
    { "url": "https://cdn.example.com/a.jpg", "type": "image" },
    { "url": "/media/b.jpg" }
  ],
  "is_announcement": false
}
```

| Trường | Kiểu | Ràng buộc |
|---|---|---|
| `family_id` | UUID | Bắt buộc, người gửi phải thuộc gia đình này |
| `content` | chuỗi | 1–20000 ký tự |
| `media` | mảng | Tối đa 20 ảnh. `url` phải là HTTPS hoặc đường dẫn nội bộ `/media/...`; `type` mặc định `image` |
| `is_announcement` | bool | Mặc định `false`, đánh dấu bài thông báo |

Phản hồi là một `PostResponse` (xem mục 2).

## 2. Xem bảng tin

`GET /api/community/posts?family_id=<UUID>&page=1&page_size=20` → **200**

Đọc từ View `community.vw_NewsfeedPosts`. View đã gộp sẵn tên tác giả, số bình luận, số cảm xúc và danh sách ảnh nên không phải gọi thêm lần nữa. Sắp xếp mới nhất trước.

```json
{
  "items": [{
    "post_id": "...", "family_id": "...", "author_id": "...",
    "author_name": "Nguyễn Văn Trường",
    "content": "Ảnh họp mặt cuối tuần",
    "created_at": "2026-11-26T03:12:00",
    "comment_count": 4, "reaction_count": 7,
    "media_urls": ["https://cdn.example.com/a.jpg"],
    "is_announcement": false,
    "my_reaction": "Love",
    "reaction_counts": { "Like": 5, "Love": 2 }
  }],
  "total": 31, "page": 1, "page_size": 20
}
```

`my_reaction` là cảm xúc của **chính người đang đăng nhập**, `null` nếu chưa thả.

## 3. Xem một bài viết

`GET /api/community/posts/{post_id}` → **200**, trả về một `PostResponse`.

## 4. Sửa bài viết

`PUT /api/community/posts/{post_id}` → **200**

Gọi `community.usp_ManagePost` với `@Action='update'`. Chỉ tác giả hoặc quản trị viên sửa được. Thân yêu cầu giống mục 1 nhưng **không gửi** `family_id`. Danh sách `media` gửi lên sẽ **thay thế toàn bộ** ảnh cũ.

## 5. Xóa bài viết

`DELETE /api/community/posts/{post_id}` → **204**

Gọi `usp_ManagePost` với `@Action='delete'`. Bình luận, cảm xúc và ảnh của bài tự xóa theo nhờ khóa ngoại `ON DELETE CASCADE`.

## 6. Bình luận

`POST /api/community/posts/{post_id}/comments` → **201**

```json
{ "content": "Ảnh đẹp quá" }
```

`content` dài 1–2000 ký tự. Phản hồi:

```json
{
  "id": "...", "post_id": "...", "user_id": "...",
  "author_name": "Trần Thị Mai", "content": "Ảnh đẹp quá",
  "created_at": "2026-11-26T03:20:00",
  "my_reaction": null, "reaction_count": 0, "reaction_counts": {}
}
```

## 7. Danh sách bình luận

`GET /api/community/posts/{post_id}/comments?page=1&page_size=50` → **200**

Trả về **mảng** `CommentResponse`, sắp xếp cũ trước. `page_size` mặc định 50.

## 8. Sửa bình luận

`PUT /api/community/comments/{comment_id}` → **204**. Gọi `usp_ManageComment` với `@Action='update'`. Thân yêu cầu: `{ "content": "..." }`.

## 9. Xóa bình luận

`DELETE /api/community/comments/{comment_id}` → **204**. Gọi `usp_ManageComment` với `@Action='delete'`.

## 10. Thả cảm xúc cho bình luận

`PUT /api/community/comments/{comment_id}/reactions` → **200**. Gọi `usp_SetCommentReaction`.

```json
{ "type": "Like" }
```

Phản hồi: `{ "comment_id": "...", "type": "Like", "reaction_count": 3, "reaction_counts": { "Like": 3 } }`

## 11. Thả cảm xúc cho bài viết

`PUT /api/community/posts/{post_id}/reactions` → **200**

Gọi `community.usp_UpsertReaction`, bên trong dùng lệnh **`MERGE`**: chưa có thì thêm, có rồi thì đổi loại. Mỗi người chỉ giữ **một** cảm xúc trên một bài, nên bấm nhiều lần cũng không sinh dòng trùng.

```json
{ "type": "Love" }
```

`type` nhận một trong `Like`, `Love`, `Haha`, `Wow`, `Sad`, `Angry`. Gửi `null` để **gỡ** cảm xúc.

```json
{ "post_id": "...", "user_id": "...", "type": "Love",
  "reaction_count": 8, "reaction_counts": { "Like": 6, "Love": 2 } }
```

## 12. Báo cáo nội dung

`POST /api/community/reports` → **201**

```json
{
  "target_id": "...",
  "target_type": "post",
  "reason": "Nội dung không phù hợp"
}
```

`target_type` nhận `post`, `comment` hoặc `photo`. `reason` dài 1–500 ký tự.

Khi một nội dung đạt **3 báo cáo đang chờ xử lý**, Trigger `community.trg_ReportedContents_Escalation` tự ghi một dòng cảnh báo vào `reports.AuditLog`. Trigger chỉ ghi đúng lúc vừa vượt ngưỡng, báo cáo thứ 4 trở đi không ghi thêm dòng trùng.

---

# Phân hệ Sự kiện — `/api/events`

## 13. Lịch sự kiện theo tháng

`GET /api/events?family_id=<UUID>&year=2026&month=11&tz_offset=420` → **200**

Gọi Function `community.fn_GetMonthlyEvents(@FamilyId, @Year, @Month)`. Hàm trả luôn số người đã nhận lời nên giao diện lịch không phải gọi thêm để đếm.

| Tham số | Ràng buộc |
|---|---|
| `year` | 1900–2200 |
| `month` | 1–12 |
| `tz_offset` | Lệch múi giờ tính bằng phút, −840 đến 840. Việt Nam là `420`. Mặc định 0 |

```json
[{
  "event_id": "...", "family_id": "...",
  "title": "Giỗ tổ", "event_date": "2026-11-30T11:00:00",
  "end_date": null, "location": "Nhà thờ họ",
  "going_count": 12, "my_rsvp": "Going"
}]
```

## 14. Tạo sự kiện

`POST /api/events` → **201**

```json
{
  "family_id": "...", "title": "Giỗ tổ",
  "event_date": "2026-11-30T11:00:00",
  "end_date": "2026-11-30T14:00:00",
  "location": "Nhà thờ họ"
}
```

`title` 1–200 ký tự, `location` 1–500 ký tự và bắt buộc. `end_date` tùy chọn nhưng nếu có thì **phải sau** `event_date`, sai sẽ trả `422`.

## 15. Xem một sự kiện

`GET /api/events/{event_id}` → **200**, trả về một `EventResponse`.

## 16. Sửa sự kiện

`PUT /api/events/{event_id}` → **200**. Gọi `community.usp_UpdateEventSchedule`. Thân yêu cầu giống mục 14 nhưng không gửi `family_id`.

## 17. Xóa sự kiện

`DELETE /api/events/{event_id}` → **204**. Gọi `usp_ManageEvent` với `@Action='delete'`. RSVP và ảnh của sự kiện tự xóa theo.

## 18. Danh sách người tham dự

`GET /api/events/{event_id}/participants?page=1&page_size=30` → **200**

```json
{
  "items": [
    { "member_id": "...", "name": "Nguyễn Văn Hùng",
      "rsvp_status": "Going", "branch_name": "Chi trưởng" }
  ],
  "total": 18,
  "counts": { "Going": 12, "Maybe": 4, "Declined": 2 }
}
```

## 19. Quản trị viên đổi trạng thái tham dự của người khác

`PUT /api/events/{event_id}/participants/{member_id}` → **204**

Gọi `usp_ManageEvent` với `@Action='participant'`. Thân yêu cầu phải có `member_id` **trùng** với `member_id` trên đường dẫn, lệch nhau sẽ trả `422`.

```json
{ "member_id": "...", "rsvp_status": "Going" }
```

## 20. Tự trả lời tham dự

`PUT /api/events/{event_id}/rsvp` → **200**

Gọi `community.usp_UpsertEventRsvp`, cũng dùng **`MERGE`**. Một thành viên chỉ có một dòng RSVP cho mỗi sự kiện, đổi ý bao nhiêu lần cũng chỉ cập nhật dòng đó. Bảng còn có ràng buộc `UNIQUE (EventId, MemberId)` chặn trùng ở mức cơ sở dữ liệu.

```json
{ "member_id": "...", "rsvp_status": "Going" }
```

`rsvp_status` nhận `Pending`, `Going`, `Maybe` hoặc `Declined`.

```json
{ "event_id": "...", "member_id": "...", "rsvp_status": "Going", "going_count": 13 }
```

## 21. Xem thư viện ảnh

`GET /api/events/{event_id}/gallery?page=1&page_size=30` → **200**, trả về mảng, mới nhất trước.

## 22. Thêm ảnh vào sự kiện

`POST /api/events/{event_id}/gallery` → **201**

```json
{ "media_url": "https://cdn.example.com/tiec.jpg" }
```

```json
{ "id": "...", "event_id": "...",
  "media_url": "https://cdn.example.com/tiec.jpg",
  "uploaded_by": "...", "created_at": "2026-11-26T04:00:00" }
```

## 23. Xóa ảnh

`DELETE /api/events/{event_id}/gallery/{gallery_id}` → **204**. Gọi `usp_ManageEvent` với `@Action='gallery-delete'`.

## 24. Xem nhắc nhở

`GET /api/events/{event_id}/reminders` → **200**

Người thường chỉ thấy nhắc nhở của chính mình và nhắc nhở chung của gia đình. Quản trị viên và trưởng họ thấy tất cả.

```json
[{ "id": "...", "event_id": "...",
   "reminder_time": "2026-11-30T09:00:00",
   "status": "pending", "user_id": "..." }]
```

`status` nhận `pending`, `sent`, `failed` hoặc `cancelled`.

## 25. Đặt nhắc nhở

`POST /api/events/{event_id}/reminders` → **201**

```json
{ "reminder_time": "2026-11-30T09:00:00", "for_family": false }
```

Đặt `for_family: true` để nhắc cả gia đình thay vì chỉ mình. Worker nền ở `apps/worker/` quét mỗi phút, tới giờ thì gửi thông báo.

Thủ tục `community.usp_ClaimDueReminders` dùng gợi ý khóa **`WITH (UPDLOCK, READPAST, ROWLOCK)`**:

- `UPDLOCK` nâng khóa đọc thành khóa cập nhật ngay lúc đọc, nên hai worker chạy song song **không cùng lấy một nhắc nhở** và không gửi trùng cho người dùng.
- `READPAST` cho worker thứ hai **bỏ qua** dòng đang bị khóa để làm tiếp thay vì đứng chờ.
- Lệnh `UPDATE ... OUTPUT` vừa đánh dấu đã gửi vừa trả dữ liệu trong một câu lệnh, không hở khoảng trống cho tranh chấp.

Đây là chỗ áp dụng trực tiếp kỹ thuật chống **mất dữ liệu cập nhật** của môn học.

## 26. Hủy nhắc nhở

`DELETE /api/events/{event_id}/reminders/{reminder_id}` → **204**. Gọi `community.usp_CancelReminder`.

---

## Đối chiếu nhanh: endpoint và đối tượng CSDL

| Đối tượng trong SQL Server | Endpoint sử dụng |
|---|---|
| View `vw_NewsfeedPosts` | 2, 3 |
| Function `fn_GetMonthlyEvents` | 13 |
| Trigger `trg_ReportedContents_Escalation` | 12 |
| `usp_CreatePostWithMedia` (giao tác, OPENJSON) | 1 |
| `usp_UpsertReaction` (MERGE) | 11 |
| `usp_UpsertEventRsvp` (MERGE) | 20 |
| `usp_ClaimDueReminders` (UPDLOCK, READPAST) | 25, worker nền |
| `usp_ManagePost`, `usp_ManageComment` | 4, 5, 8, 9 |
| `usp_ManageEvent`, `usp_UpdateEventSchedule` | 16, 17, 19, 23 |
| `usp_SetCommentReaction`, `usp_CancelReminder` | 10, 26 |

## Kiểm thử

- `tests/api/test_community_events_api.py` — kiểm thử API bằng phiên cơ sở dữ liệu giả, chạy được mà không cần SQL Server.
- `tests/database/test_community_smoke.sql` — chạy thử trực tiếp trên SQL Server, cuối file có `ROLLBACK` nên không để lại dữ liệu.
