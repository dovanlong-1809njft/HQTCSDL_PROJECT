# Structure Inventory — Kiểm kê cấu trúc FamilyConnect

> Được tạo bằng cách duyệt **file đang có trong ZIP cập nhật**, không sao chép số đếm từ bản cũ. **Không có file nào bị xóa** trong đợt đồng bộ tài liệu 16/10/2026.

- **Tổng số file:** 242 (bao gồm chính file kiểm kê này và các file Markdown mới).
- **Tổng số thư mục con:** 28 (không tính thư mục gốc `FamilyConnect/`).
- **Nguồn đối chiếu:** `FamilyConnect_Frontend(3).zip` + các file tài liệu mới/cập nhật trong đợt này.
- **Ý nghĩa:** Một đường dẫn có mặt **không** đồng nghĩa tính năng đã chạy hoàn chỉnh.

## File theo nhóm thư mục

### (gốc) — 4 file

- `.env.example`
- `.gitignore`
- `README.md`
- `docker-compose.yml`

### .github — 4 file

- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `.github/pull_request_template.md`
- `.github/workflows/ci.yml`

### backend — 77 file

- `backend/.dockerignore`
- `backend/Dockerfile`
- `backend/app/__init__.py`
- `backend/app/config.py`
- `backend/app/core/__init__.py`
- `backend/app/core/dependencies.py`
- `backend/app/core/exceptions.py`
- `backend/app/core/permissions.py`
- `backend/app/core/security.py`
- `backend/app/db/__init__.py`
- `backend/app/db/connection.py`
- `backend/app/integrations/__init__.py`
- `backend/app/integrations/embedding_client.py`
- `backend/app/integrations/llm_client.py`
- `backend/app/jobs/__init__.py`
- `backend/app/jobs/event_reminders.py`
- `backend/app/main.py`
- `backend/app/repositories/__init__.py`
- `backend/app/repositories/admin_repository.py`
- `backend/app/repositories/ai_repository.py`
- `backend/app/repositories/community_repository.py`
- `backend/app/repositories/dashboard_repository.py`
- `backend/app/repositories/directory_repository.py`
- `backend/app/repositories/event_repository.py`
- `backend/app/repositories/family_repository.py`
- `backend/app/repositories/genealogy_repository.py`
- `backend/app/repositories/heritage_repository.py`
- `backend/app/repositories/media_repository.py`
- `backend/app/repositories/notification_repository.py`
- `backend/app/repositories/user_repository.py`
- `backend/app/routers/__init__.py`
- `backend/app/routers/admin.py`
- `backend/app/routers/ai.py`
- `backend/app/routers/auth.py`
- `backend/app/routers/community.py`
- `backend/app/routers/dashboard.py`
- `backend/app/routers/directory.py`
- `backend/app/routers/events.py`
- `backend/app/routers/families.py`
- `backend/app/routers/genealogy.py`
- `backend/app/routers/heritage.py`
- `backend/app/routers/media.py`
- `backend/app/routers/notifications.py`
- `backend/app/routers/users.py`
- `backend/app/schemas/__init__.py`
- `backend/app/schemas/admin_schema.py`
- `backend/app/schemas/ai_schema.py`
- `backend/app/schemas/auth_schema.py`
- `backend/app/schemas/dashboard_schema.py`
- `backend/app/schemas/directory_schema.py`
- `backend/app/schemas/event_schema.py`
- `backend/app/schemas/family_schema.py`
- `backend/app/schemas/genealogy_schema.py`
- `backend/app/schemas/heritage_schema.py`
- `backend/app/schemas/media_schema.py`
- `backend/app/schemas/notification_schema.py`
- `backend/app/schemas/post_schema.py`
- `backend/app/schemas/user_schema.py`
- `backend/app/services/__init__.py`
- `backend/app/services/admin_service.py`
- `backend/app/services/ai_service.py`
- `backend/app/services/auth_service.py`
- `backend/app/services/community_service.py`
- `backend/app/services/dashboard_service.py`
- `backend/app/services/directory_service.py`
- `backend/app/services/event_service.py`
- `backend/app/services/family_service.py`
- `backend/app/services/genealogy_service.py`
- `backend/app/services/heritage_service.py`
- `backend/app/services/media_service.py`
- `backend/app/services/notification_service.py`
- `backend/app/services/report_service.py`
- `backend/app/services/search_service.py`
- `backend/app/services/user_service.py`
- `backend/requirements-ai.txt`
- `backend/requirements-dev.txt`
- `backend/requirements.txt`

### database — 20 file

- `database/01_create_database.sql`
- `database/02_create_tables.sql`
- `database/03_constraints_indexes.sql`
- `database/04_seed_data.sql`
- `database/05_views.sql`
- `database/06_functions.sql`
- `database/07_stored_procedures.sql`
- `database/08_triggers.sql`
- `database/09_transactions.sql`
- `database/10_reports.sql`
- `database/11_security.sql`
- `database/12_backup.sql`
- `database/13_restore.sql`
- `database/README.md`
- `database/tests/test_concurrency.sql`
- `database/tests/test_constraints.sql`
- `database/tests/test_genealogy.sql`
- `database/tests/test_permissions.sql`
- `database/tests/test_restore.sql`
- `database/tests/test_transactions.sql`

### docs — 49 file

- `docs/CHANGELOG_STRUCTURE.md`
- `docs/DEVELOPMENT_HISTORY.md`
- `docs/DOCUMENT_AUDIT.md`
- `docs/DOCUMENT_REVIEW_CANDIDATES.md`
- `docs/FRONTEND_BAOCAO.md`
- `docs/FRONTEND_CAYGIAPHA.md`
- `docs/FRONTEND_CONGDONG.md`
- `docs/FRONTEND_DANGNHAP_TAIKHOAN.md`
- `docs/FRONTEND_DANHBA.md`
- `docs/FRONTEND_DARK_MODE_V5.md`
- `docs/FRONTEND_DISAN.md`
- `docs/FRONTEND_FEATURE_MATRIX.md`
- `docs/FRONTEND_GIADINH.md`
- `docs/FRONTEND_HOSO.md`
- `docs/FRONTEND_QUANTRI.md`
- `docs/FRONTEND_SIDEBAR.md`
- `docs/FRONTEND_STEP1.md`
- `docs/FRONTEND_SUKIEN.md`
- `docs/FRONTEND_THONGBAO.md`
- `docs/FRONTEND_TROLYAI.md`
- `docs/FRONTEND_UI_FIXES_V3.md`
- `docs/PROJECT_STATUS.md`
- `docs/README.md`
- `docs/SCAFFOLD_STATUS.md`
- `docs/VALIDATION.md`
- `docs/ai-design.md`
- `docs/api-documentation.md`
- `docs/architecture.md`
- `docs/backup-restore.md`
- `docs/database-design.md`
- `docs/decision-log.md`
- `docs/dependencies.md`
- `docs/deployment-guide.md`
- `docs/diagrams/.gitkeep`
- `docs/diagrams/README.md`
- `docs/diagrams/architecture.mmd`
- `docs/diagrams/genealogy-core.mmd`
- `docs/file-guide.md`
- `docs/file-ownership.md`
- `docs/implementation-order.md`
- `docs/requirements.md`
- `docs/structure-inventory.md`
- `docs/sw.js`
- `docs/task-checklist.txt`
- `docs/team-guide.md`
- `docs/terms-quick-reference.txt`
- `docs/test-report.md`
- `docs/use-cases.md`
- `docs/user-guide.md`

### frontend — 70 file

- `frontend/README.md`
- `frontend/assets/css/account-menu.css`
- `frontend/assets/css/admin.css`
- `frontend/assets/css/ai.css`
- `frontend/assets/css/auth-page.css`
- `frontend/assets/css/community.css`
- `frontend/assets/css/directory.css`
- `frontend/assets/css/events.css`
- `frontend/assets/css/family.css`
- `frontend/assets/css/genealogy.css`
- `frontend/assets/css/heritage.css`
- `frontend/assets/css/main.css`
- `frontend/assets/css/notification-popover.css`
- `frontend/assets/css/notifications.css`
- `frontend/assets/css/profile.css`
- `frontend/assets/css/reports.css`
- `frontend/assets/css/responsive.css`
- `frontend/assets/css/sidebar.css`
- `frontend/assets/css/theme.css`
- `frontend/assets/icons/.gitkeep`
- `frontend/assets/icons/README.md`
- `frontend/assets/images/.gitkeep`
- `frontend/assets/images/community-gathering.svg`
- `frontend/assets/images/community-memory.svg`
- `frontend/assets/images/community-travel.svg`
- `frontend/assets/images/heritage-archive.svg`
- `frontend/assets/js/core/account-menu.js`
- `frontend/assets/js/core/api.js`
- `frontend/assets/js/core/auth.js`
- `frontend/assets/js/core/event-store.js`
- `frontend/assets/js/core/family-store.js`
- `frontend/assets/js/core/media.js`
- `frontend/assets/js/core/notification-popover.js`
- `frontend/assets/js/core/notification-store.js`
- `frontend/assets/js/core/profile-badge.js`
- `frontend/assets/js/core/pwa.js`
- `frontend/assets/js/core/report-math.js`
- `frontend/assets/js/core/sidebar.js`
- `frontend/assets/js/core/ui.js`
- `frontend/assets/js/main.js`
- `frontend/assets/js/modules/account.js`
- `frontend/assets/js/modules/admin.js`
- `frontend/assets/js/modules/ai.js`
- `frontend/assets/js/modules/auth-page.js`
- `frontend/assets/js/modules/community.js`
- `frontend/assets/js/modules/dashboard.js`
- `frontend/assets/js/modules/directory.js`
- `frontend/assets/js/modules/events.js`
- `frontend/assets/js/modules/family.js`
- `frontend/assets/js/modules/genealogy.js`
- `frontend/assets/js/modules/heritage.js`
- `frontend/assets/js/modules/notifications.js`
- `frontend/assets/js/modules/reports.js`
- `frontend/index.html`
- `frontend/manifest.json`
- `frontend/pages/admin.html`
- `frontend/pages/ai-assistant.html`
- `frontend/pages/community.html`
- `frontend/pages/dashboard.html`
- `frontend/pages/directory.html`
- `frontend/pages/events.html`
- `frontend/pages/family.html`
- `frontend/pages/genealogy.html`
- `frontend/pages/heritage.html`
- `frontend/pages/login.html`
- `frontend/pages/notifications.html`
- `frontend/pages/profile.html`
- `frontend/pages/register.html`
- `frontend/pages/reports.html`
- `frontend/sw.js`

### scripts — 3 file

- `scripts/check_db_connection.py`
- `scripts/check_structure.py`
- `scripts/rebuild_search_index.py`

### tests — 15 file

- `tests/README.md`
- `tests/conftest.py`
- `tests/test_admin.py`
- `tests/test_ai.py`
- `tests/test_auth.py`
- `tests/test_community.py`
- `tests/test_directory.py`
- `tests/test_events.py`
- `tests/test_families.py`
- `tests/test_genealogy.py`
- `tests/test_heritage.py`
- `tests/test_media.py`
- `tests/test_notifications.py`
- `tests/test_permissions.py`
- `tests/test_reports.py`

## Khi thêm hoặc xóa file lần tới

Đếm lại từ cây thư mục thật, cập nhật đồng thời `file-ownership.md` và `PROJECT_STATUS.md`. Nếu dùng Python trong thư mục `FamilyConnect`:

```powershell
py -c "from pathlib import Path; print(sum(p.is_file() for p in Path('.').rglob('*')))"
```

Nếu có yêu cầu xóa/chuyển file, xem `DOCUMENT_REVIEW_CANDIDATES.md` và xin duyệt trước.
