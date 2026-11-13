# Tích hợp vào nhánh dovanlong — 14/11/2026
---
# TV4 — Đỗ Văn Long
## Đối chiếu phân công
| Dòng | Công việc | Mã bàn giao | Mức xác minh |
|---|---|---|---|
| 23 | Schema/seed, view window ranking, trigger | Giữ nguyên schema/seed; 3 view TV4, trigger Honors nhiều dòng | ScriptDom PASS; thực thi SQL NOT RUN |
| 24 | Ba SP di sản/vinh danh/cây JSON | Ba SP yêu cầu + update/delete + helper kiểm tra quyền/payload | ScriptDom PASS; SQL runtime/đồng thời NOT RUN |
| 25 | API, Web và Mobile di sản/vinh danh | API đầy đủ, Web CRUD/filter/ranking/detail, module React Native riêng | API contract/Web build/UI PASS; Mobile runtime BLOCKED |
| 26 | Cây lớn, React Flow, pan/zoom/animation/API | Fixture 1.023 node/10 thế hệ, layout và màn Web dùng API | Unit và UI PASS; end-to-end SQL NOT RUN |

## File gốc chỉnh sửa (10)

| File | Thay đổi |
|---|---|
| `database/views/04_heritage_views.sql` | Ranking DENSE_RANK và hai view fingerprint |
| `database/procedures/04_heritage_procs.sql` | CRUD TV4, kiểm tra quyền/payload, xuất cây JSON |
| `database/triggers/04_heritage_triggers.sql` | Honors validation + audit INSERT/UPDATE/DELETE nhiều dòng |
| `apps/backend/app/domains/heritage/schemas.py` | DTO, kiểm tra media/payload, response/pagination/tree |
| `apps/backend/app/domains/heritage/repository.py` | Bound T-SQL queries/SP |
| `apps/backend/app/domains/heritage/services.py` | PATCH merge, transaction, ánh xạ lỗi |
| `apps/backend/app/domains/heritage/router.py` | Endpoint TV4, JWT/RBAC dùng lại TV1 |
| `apps/backend/app/api/router.py` | **Dùng chung:** import/mount heritage router |
| `apps/web/src/app/App.jsx` | **Dùng chung:** hai lazy route trong guard hiện tại |
| `apps/web/src/shared/layouts/Sidebar.jsx` | **Dùng chung:** bật hai mục TV4; giữ các mục khác |

## File mới (20)

- `apps/web/src/features/heritage/api/heritageApi.js`
- `apps/web/src/features/heritage/components/FamilyScope.jsx`
- `apps/web/src/features/heritage/components/HeritageForm.jsx`
- `apps/web/src/features/heritage/pages/Heritage.jsx`
- `apps/web/src/features/family-tree/layout.mjs`
- `apps/web/src/features/family-tree/pages/FamilyTree.jsx`
- `apps/mobile/src/features/heritage/api.js`
- `apps/mobile/src/features/heritage/HeritageScreen.jsx`
- `apps/mobile/src/features/heritage/README.md`
- `packages/mock-data/generate-tv4-tree.mjs`
- `packages/mock-data/tv4-family-tree-large.json`
- `tests/api/test_heritage.py`
- `tests/unit/tv4-tree.test.mjs`
- `tests/e2e/test_tv4_ui.py`
- `tests/database/tv4.static.ps1`
- `tests/database/tv4.integration.sql`
- `TV4_CHANGELOG.md`

Không sửa `dependencies.py`, API client dùng chung, package/lock/requirements,
schema, seed, init script, permissions hoặc domain của TV1/TV2/TV3/TV5.
Không xóa/đổi tên file gốc, kể cả `.gitkeep`.
`.venv`, `node_modules`, `dist`, cache Python là sản phẩm cục bộ được `.gitignore`
hiện có loại trừ. Cache npm tạm tạo cho lần cài đặt đã được dọn.
