# Bảng tin (Newsfeed) — Mobile, TV3

Màn hình bảng tin của gia đình: xem bài viết, đăng bài, bình luận, thả cảm xúc.

| File | Vai trò |
|---|---|
| `NewsfeedScreen.jsx` | Màn hình chính: danh sách bài, ô soạn bài, modal bình luận |
| `PostCard.jsx` | Một thẻ bài viết: ảnh, cảm xúc, số bình luận |
| `api.js` | Gọi API `/api/community/...` |

Dùng:

```jsx
<NewsfeedScreen familyId={familyId} />
```

Trước đó gọi `setAccessToken(token)` trong `src/core/api.js` sau khi đăng nhập,
vì mọi API đều yêu cầu JWT.

Màn hình viết bằng React Native thuần (không thêm thư viện ngoài). Khung ứng
dụng mobile (Expo/React Native CLI, điều hướng) do TV2 khởi tạo; khi khung có
rồi thì đưa hai màn hình này vào tab tương ứng.
