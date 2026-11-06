from fastapi import HTTPException, status


class DomainError(Exception):
    """Ngoại lệ tầng miền nghiệp vụ (Domain Layer)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Không tìm thấy tài nguyên yêu cầu.") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(HTTPException):
    def __init__(self, detail: str = "Dữ liệu bị trùng lặp hoặc xung đột.") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
