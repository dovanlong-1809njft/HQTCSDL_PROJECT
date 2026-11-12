# Lịch sự kiện & Thư viện ảnh — Mobile, TV3

| File | Vai trò |
|---|---|
| `CalendarScreen.jsx` | Lưới lịch tháng, chấm dấu ngày có sự kiện, danh sách sự kiện |
| `EventDetail.jsx` | Chi tiết sự kiện: RSVP, thư viện ảnh, đặt nhắc nhở |
| `api.js` | Gọi API `/api/events/...` |

Dùng:

```jsx
<CalendarScreen familyId={familyId} memberId={memberId} />
```

`memberId` là `genealogy.Members.Id` chứ không phải `UserId`, vì bảng
`EventParticipants` tham chiếu tới thành viên gia phả.

Lịch tháng đọc qua Function `community.fn_GetMonthlyEvents`, nên mỗi ô ngày đã
có sẵn số người trả lời "Going" mà không cần gọi thêm API.
