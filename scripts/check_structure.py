"""Kiểm tra khung/cú pháp; KHÔNG kiểm thử chức năng hoặc kết nối CSDL."""
from pathlib import Path
import ast
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ["README.md", ".env.example", "backend/app/main.py", "backend/app/db/connection.py",
            "backend/app/routers/media.py", "backend/app/jobs/event_reminders.py",
            "frontend/pages/profile.html", "frontend/pages/notifications.html", "frontend/pages/reports.html",
            "database/01_create_database.sql", "database/12_backup.sql", "database/13_restore.sql",
            "docs/requirements.md", "docs/api-documentation.md", "docs/file-ownership.md"]
errors = []
for name in REQUIRED:
    if not (ROOT / name).is_file():
        errors.append("Thiếu " + name)
files = [p for p in ROOT.rglob("*") if p.is_file()
         and not any(part in {".git", ".venv", "venv", "__pycache__", "node_modules"}
                     for part in p.relative_to(ROOT).parts)]
python_count = 0
for path in files:
    try:
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            python_count += 1
        elif path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8-sig"))
    except (SyntaxError, UnicodeError, ValueError) as exc:
        errors.append(str(path.relative_to(ROOT)) + ": " + str(exc))
if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"Đạt kiểm tra khung: {python_count} tệp Python hợp lệ cú pháp; JSON đọc được.")
print("KHÔNG phải kết quả kiểm thử API, SQL Server, AI, Docker hoặc PWA.")
