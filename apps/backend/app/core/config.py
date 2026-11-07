import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    repo_env = Path(__file__).resolve().parents[4] / ".env"
    if repo_env.exists():
        load_dotenv(repo_env)
    else:
        load_dotenv()
except ImportError:
    pass

MSSQL_USER = os.getenv("MSSQL_USER", "sa")
MSSQL_SA_PASSWORD = os.getenv("MSSQL_SA_PASSWORD", "")
MSSQL_HOST = os.getenv("MSSQL_HOST", "localhost")
MSSQL_PORT = int(os.getenv("MSSQL_PORT", "1433"))
MSSQL_DB = os.getenv("MSSQL_DB", "FamilyConnect")
MSSQL_TRUSTED_CONNECTION = os.getenv("MSSQL_TRUSTED_CONNECTION", "no").strip().lower() in {"1", "true", "yes"}

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError("Thiếu JWT_SECRET_KEY. Hãy cấu hình biến môi trường trước khi chạy backend.")

ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
GEMINI_EMBEDDING_DIM = int(os.getenv("GEMINI_EMBEDDING_DIM", "256"))
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
