"""Khởi chạy API FastAPI — hiện chỉ cung cấp endpoint kiểm tra sức khỏe."""
from fastapi import FastAPI

app = FastAPI(title="FamilyConnect API", version="0.1.0")

@app.get("/health", tags=["System"])
def health_check():
    """Kiểm tra API đang chạy, CHƯA xác nhận kết nối SQL Server."""
    return {"status": "ok", "service": "FamilyConnect", "database": "not_checked"}

# TODO: Thêm routers khi các module được triển khai và kiểm thử.
