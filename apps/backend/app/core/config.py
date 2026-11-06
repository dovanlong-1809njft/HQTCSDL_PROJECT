import os

MSSQL_USER = os.getenv("MSSQL_USER", "sa")
MSSQL_SA_PASSWORD = os.getenv("MSSQL_SA_PASSWORD", "")
MSSQL_HOST = os.getenv("MSSQL_HOST", "localhost")
MSSQL_PORT = int(os.getenv("MSSQL_PORT", "1433"))
MSSQL_DB = os.getenv("MSSQL_DB", "FamilyConnect")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError("Thiếu JWT_SECRET_KEY. Hãy cấu hình biến môi trường trước khi chạy backend.")

ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
