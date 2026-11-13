# TV4 — module React Native

Host ứng dụng/Navigation vẫn thuộc TV2. Module này không tạo package hay app mới.

```jsx
const heritageApi = useMemo(() => createHeritageApi({
  getAccessToken: () => auth.currentAccessToken,
  baseUrl: 'https://your-api.example/api',
}), [auth.currentAccessToken]);
<HeritageScreen api={heritageApi} user={{ id: auth.user.id, role: auth.user.role }} />
```

Đăng ký screen trong navigation của host; truyền instance API ổn định và user từ JWT.
API adapter hỗ trợ GET/POST/PATCH/DELETE, URL/query và token hiện tại; không sửa adapter của TV3.
UI có danh sách, chi tiết, lọc, phân trang, CRUD di sản/vinh danh, xếp hạng. Vinh danh mới
nhập UUID hồ sơ lấy từ danh bạ TV2; trường này không phải UserId. Mobile chỉ mở media
HTTPS đầy đủ; `/media/` cần host chuyển thành URL server hợp lệ. Không có upload storage.

HTTP contract giống Web, xem README_TV4_RUN.md. Backend quyết định quyền, UI chỉ ẩn nút.
Chưa chạy React Native hoặc E2E Mobile: **BLOCKED** do thiếu app host/package và emulator.
