# Danh mục — frontend bước 1

28 thư mục con, 193 tệp; không tính gốc FamilyConnect.

## Thư mục

- `.github/`
- `.github/ISSUE_TEMPLATE/`
- `.github/workflows/`
- `backend/`
- `backend/app/`
- `backend/app/core/`
- `backend/app/db/`
- `backend/app/integrations/`
- `backend/app/jobs/`
- `backend/app/repositories/`
- `backend/app/routers/`
- `backend/app/schemas/`
- `backend/app/services/`
- `database/`
- `database/tests/`
- `docs/`
- `docs/diagrams/`
- `frontend/`
- `frontend/assets/`
- `frontend/assets/css/`
- `frontend/assets/icons/`
- `frontend/assets/images/`
- `frontend/assets/js/`
- `frontend/assets/js/core/`
- `frontend/assets/js/modules/`
- `frontend/pages/`
- `scripts/`
- `tests/`

## Tệp

| STT | Đường dẫn | Loại | Đầu mối |
|---:|---|---|---|
| 1 | `.env.example` | Cấu hình | B |
| 2 | `.github/ISSUE_TEMPLATE/bug_report.md` | Tài liệu/sơ đồ | E |
| 3 | `.github/ISSUE_TEMPLATE/feature_request.md` | Tài liệu/sơ đồ | E |
| 4 | `.github/pull_request_template.md` | Tài liệu/sơ đồ | E |
| 5 | `.github/workflows/ci.yml` | Cấu hình | E |
| 6 | `.gitignore` | Cấu hình | E |
| 7 | `README.md` | Tài liệu/sơ đồ | E |
| 8 | `backend/.dockerignore` | Cấu hình | E |
| 9 | `backend/Dockerfile` | Cấu hình | E |
| 10 | `backend/app/__init__.py` | Python | B |
| 11 | `backend/app/config.py` | Python | B |
| 12 | `backend/app/core/__init__.py` | Python | B |
| 13 | `backend/app/core/dependencies.py` | Python | B |
| 14 | `backend/app/core/exceptions.py` | Python | B |
| 15 | `backend/app/core/permissions.py` | Python | B |
| 16 | `backend/app/core/security.py` | Python | B |
| 17 | `backend/app/db/__init__.py` | Python | B |
| 18 | `backend/app/db/connection.py` | Python | B |
| 19 | `backend/app/integrations/__init__.py` | Python | E |
| 20 | `backend/app/integrations/embedding_client.py` | Python | E |
| 21 | `backend/app/integrations/llm_client.py` | Python | E |
| 22 | `backend/app/jobs/__init__.py` | Python | E |
| 23 | `backend/app/jobs/event_reminders.py` | Python | E |
| 24 | `backend/app/main.py` | Python | B |
| 25 | `backend/app/repositories/__init__.py` | Python | B |
| 26 | `backend/app/repositories/admin_repository.py` | Python | B |
| 27 | `backend/app/repositories/ai_repository.py` | Python | E |
| 28 | `backend/app/repositories/community_repository.py` | Python | D |
| 29 | `backend/app/repositories/dashboard_repository.py` | Python | E |
| 30 | `backend/app/repositories/directory_repository.py` | Python | C |
| 31 | `backend/app/repositories/event_repository.py` | Python | D |
| 32 | `backend/app/repositories/family_repository.py` | Python | B |
| 33 | `backend/app/repositories/genealogy_repository.py` | Python | C |
| 34 | `backend/app/repositories/heritage_repository.py` | Python | E |
| 35 | `backend/app/repositories/media_repository.py` | Python | D |
| 36 | `backend/app/repositories/notification_repository.py` | Python | E |
| 37 | `backend/app/repositories/user_repository.py` | Python | B |
| 38 | `backend/app/routers/__init__.py` | Python | B |
| 39 | `backend/app/routers/admin.py` | Python | B |
| 40 | `backend/app/routers/ai.py` | Python | E |
| 41 | `backend/app/routers/auth.py` | Python | B |
| 42 | `backend/app/routers/community.py` | Python | D |
| 43 | `backend/app/routers/dashboard.py` | Python | E |
| 44 | `backend/app/routers/directory.py` | Python | C |
| 45 | `backend/app/routers/events.py` | Python | D |
| 46 | `backend/app/routers/families.py` | Python | B |
| 47 | `backend/app/routers/genealogy.py` | Python | C |
| 48 | `backend/app/routers/heritage.py` | Python | E |
| 49 | `backend/app/routers/media.py` | Python | D |
| 50 | `backend/app/routers/notifications.py` | Python | E |
| 51 | `backend/app/routers/users.py` | Python | B |
| 52 | `backend/app/schemas/__init__.py` | Python | B |
| 53 | `backend/app/schemas/admin_schema.py` | Python | B |
| 54 | `backend/app/schemas/ai_schema.py` | Python | E |
| 55 | `backend/app/schemas/auth_schema.py` | Python | B |
| 56 | `backend/app/schemas/dashboard_schema.py` | Python | E |
| 57 | `backend/app/schemas/directory_schema.py` | Python | C |
| 58 | `backend/app/schemas/event_schema.py` | Python | D |
| 59 | `backend/app/schemas/family_schema.py` | Python | B |
| 60 | `backend/app/schemas/genealogy_schema.py` | Python | C |
| 61 | `backend/app/schemas/heritage_schema.py` | Python | E |
| 62 | `backend/app/schemas/media_schema.py` | Python | D |
| 63 | `backend/app/schemas/notification_schema.py` | Python | E |
| 64 | `backend/app/schemas/post_schema.py` | Python | D |
| 65 | `backend/app/schemas/user_schema.py` | Python | B |
| 66 | `backend/app/services/__init__.py` | Python | B |
| 67 | `backend/app/services/admin_service.py` | Python | B |
| 68 | `backend/app/services/ai_service.py` | Python | E |
| 69 | `backend/app/services/auth_service.py` | Python | B |
| 70 | `backend/app/services/community_service.py` | Python | D |
| 71 | `backend/app/services/dashboard_service.py` | Python | E |
| 72 | `backend/app/services/directory_service.py` | Python | C |
| 73 | `backend/app/services/event_service.py` | Python | D |
| 74 | `backend/app/services/family_service.py` | Python | B |
| 75 | `backend/app/services/genealogy_service.py` | Python | C |
| 76 | `backend/app/services/heritage_service.py` | Python | E |
| 77 | `backend/app/services/media_service.py` | Python | D |
| 78 | `backend/app/services/notification_service.py` | Python | E |
| 79 | `backend/app/services/report_service.py` | Python | E |
| 80 | `backend/app/services/search_service.py` | Python | E |
| 81 | `backend/app/services/user_service.py` | Python | B |
| 82 | `backend/requirements-ai.txt` | Cấu hình | E |
| 83 | `backend/requirements-dev.txt` | Cấu hình | E |
| 84 | `backend/requirements.txt` | Cấu hình | B |
| 85 | `database/01_create_database.sql` | T-SQL | A |
| 86 | `database/02_create_tables.sql` | T-SQL | A |
| 87 | `database/03_constraints_indexes.sql` | T-SQL | A |
| 88 | `database/04_seed_data.sql` | T-SQL | A |
| 89 | `database/05_views.sql` | T-SQL | A |
| 90 | `database/06_functions.sql` | T-SQL | A |
| 91 | `database/07_stored_procedures.sql` | T-SQL | A |
| 92 | `database/08_triggers.sql` | T-SQL | A |
| 93 | `database/09_transactions.sql` | T-SQL | A |
| 94 | `database/10_reports.sql` | T-SQL | A |
| 95 | `database/11_security.sql` | T-SQL | A |
| 96 | `database/12_backup.sql` | T-SQL | A |
| 97 | `database/13_restore.sql` | T-SQL | A |
| 98 | `database/README.md` | Tài liệu/sơ đồ | A |
| 99 | `database/tests/test_concurrency.sql` | Khung kiểm thử | A |
| 100 | `database/tests/test_constraints.sql` | Khung kiểm thử | A |
| 101 | `database/tests/test_genealogy.sql` | Khung kiểm thử | A |
| 102 | `database/tests/test_permissions.sql` | Khung kiểm thử | A |
| 103 | `database/tests/test_restore.sql` | Khung kiểm thử | A |
| 104 | `database/tests/test_transactions.sql` | Khung kiểm thử | A |
| 105 | `docker-compose.yml` | Cấu hình | E |
| 106 | `docs/CHANGELOG_STRUCTURE.md` | Tài liệu/sơ đồ | E |
| 107 | `docs/FRONTEND_STEP1.md` | Tài liệu/sơ đồ | D |
| 108 | `docs/README.md` | Tài liệu/sơ đồ | E |
| 109 | `docs/SCAFFOLD_STATUS.md` | Tài liệu/sơ đồ | E |
| 110 | `docs/VALIDATION.md` | Tài liệu/sơ đồ | E |
| 111 | `docs/ai-design.md` | Tài liệu/sơ đồ | E |
| 112 | `docs/api-documentation.md` | Tài liệu/sơ đồ | B |
| 113 | `docs/architecture.md` | Tài liệu/sơ đồ | B |
| 114 | `docs/backup-restore.md` | Tài liệu/sơ đồ | A |
| 115 | `docs/database-design.md` | Tài liệu/sơ đồ | A |
| 116 | `docs/decision-log.md` | Tài liệu/sơ đồ | E |
| 117 | `docs/dependencies.md` | Tài liệu/sơ đồ | E |
| 118 | `docs/deployment-guide.md` | Tài liệu/sơ đồ | E |
| 119 | `docs/diagrams/.gitkeep` | Giữ thư mục | E |
| 120 | `docs/diagrams/README.md` | Tài liệu/sơ đồ | E |
| 121 | `docs/diagrams/architecture.mmd` | Tài liệu/sơ đồ | E |
| 122 | `docs/diagrams/genealogy-core.mmd` | Tài liệu/sơ đồ | A |
| 123 | `docs/file-guide.md` | Tài liệu/sơ đồ | E |
| 124 | `docs/file-ownership.md` | Tài liệu/sơ đồ | E |
| 125 | `docs/implementation-order.md` | Tài liệu/sơ đồ | E |
| 126 | `docs/requirements.md` | Tài liệu/sơ đồ | E |
| 127 | `docs/structure-inventory.md` | Tài liệu/sơ đồ | E |
| 128 | `docs/task-checklist.txt` | Tài liệu/sơ đồ | E |
| 129 | `docs/team-guide.md` | Tài liệu/sơ đồ | E |
| 130 | `docs/terms-quick-reference.txt` | Tài liệu/sơ đồ | E |
| 131 | `docs/test-report.md` | Tài liệu/sơ đồ | E |
| 132 | `docs/use-cases.md` | Tài liệu/sơ đồ | E |
| 133 | `docs/user-guide.md` | Tài liệu/sơ đồ | E |
| 134 | `frontend/README.md` | Tài liệu/sơ đồ | D |
| 135 | `frontend/assets/css/genealogy.css` | Giao diện | C |
| 136 | `frontend/assets/css/main.css` | Giao diện | D |
| 137 | `frontend/assets/css/responsive.css` | Giao diện | D |
| 138 | `frontend/assets/icons/.gitkeep` | Giữ thư mục | D |
| 139 | `frontend/assets/icons/README.md` | Tài liệu/sơ đồ | D |
| 140 | `frontend/assets/images/.gitkeep` | Giữ thư mục | D |
| 141 | `frontend/assets/js/core/api.js` | Giao diện | D |
| 142 | `frontend/assets/js/core/auth.js` | Giao diện | D |
| 143 | `frontend/assets/js/core/media.js` | Giao diện | D |
| 144 | `frontend/assets/js/core/pwa.js` | Giao diện | D |
| 145 | `frontend/assets/js/core/ui.js` | Giao diện | D |
| 146 | `frontend/assets/js/main.js` | Giao diện | D |
| 147 | `frontend/assets/js/modules/account.js` | Giao diện | D |
| 148 | `frontend/assets/js/modules/admin.js` | Giao diện | B |
| 149 | `frontend/assets/js/modules/ai.js` | Giao diện | E |
| 150 | `frontend/assets/js/modules/community.js` | Giao diện | D |
| 151 | `frontend/assets/js/modules/dashboard.js` | Giao diện | E |
| 152 | `frontend/assets/js/modules/directory.js` | Giao diện | C |
| 153 | `frontend/assets/js/modules/events.js` | Giao diện | D |
| 154 | `frontend/assets/js/modules/family.js` | Giao diện | B |
| 155 | `frontend/assets/js/modules/genealogy.js` | Giao diện | C |
| 156 | `frontend/assets/js/modules/heritage.js` | Giao diện | E |
| 157 | `frontend/assets/js/modules/notifications.js` | Giao diện | E |
| 158 | `frontend/assets/js/modules/reports.js` | Giao diện | E |
| 159 | `frontend/index.html` | Giao diện | D |
| 160 | `frontend/manifest.json` | Cấu hình | D |
| 161 | `frontend/pages/admin.html` | Giao diện | B |
| 162 | `frontend/pages/ai-assistant.html` | Giao diện | E |
| 163 | `frontend/pages/community.html` | Giao diện | D |
| 164 | `frontend/pages/dashboard.html` | Giao diện | E |
| 165 | `frontend/pages/directory.html` | Giao diện | C |
| 166 | `frontend/pages/events.html` | Giao diện | D |
| 167 | `frontend/pages/family.html` | Giao diện | B |
| 168 | `frontend/pages/genealogy.html` | Giao diện | C |
| 169 | `frontend/pages/heritage.html` | Giao diện | E |
| 170 | `frontend/pages/login.html` | Giao diện | D |
| 171 | `frontend/pages/notifications.html` | Giao diện | E |
| 172 | `frontend/pages/profile.html` | Giao diện | D |
| 173 | `frontend/pages/register.html` | Giao diện | D |
| 174 | `frontend/pages/reports.html` | Giao diện | E |
| 175 | `frontend/sw.js` | Giao diện | D |
| 176 | `scripts/check_db_connection.py` | Python | B |
| 177 | `scripts/check_structure.py` | Python | E |
| 178 | `scripts/rebuild_search_index.py` | Python | E |
| 179 | `tests/README.md` | Tài liệu/sơ đồ | E |
| 180 | `tests/conftest.py` | Khung kiểm thử | E |
| 181 | `tests/test_admin.py` | Khung kiểm thử | B |
| 182 | `tests/test_ai.py` | Khung kiểm thử | E |
| 183 | `tests/test_auth.py` | Khung kiểm thử | B |
| 184 | `tests/test_community.py` | Khung kiểm thử | D |
| 185 | `tests/test_directory.py` | Khung kiểm thử | C |
| 186 | `tests/test_events.py` | Khung kiểm thử | D |
| 187 | `tests/test_families.py` | Khung kiểm thử | B |
| 188 | `tests/test_genealogy.py` | Khung kiểm thử | C |
| 189 | `tests/test_heritage.py` | Khung kiểm thử | E |
| 190 | `tests/test_media.py` | Khung kiểm thử | D |
| 191 | `tests/test_notifications.py` | Khung kiểm thử | E |
| 192 | `tests/test_permissions.py` | Khung kiểm thử | B |
| 193 | `tests/test_reports.py` | Khung kiểm thử | E |
