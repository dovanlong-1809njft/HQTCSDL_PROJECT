# Dieu phoi nghiep vu / goi SDK ben ngoai cho domain genealogy
import re
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.domains.genealogy import repository
from app.domains.genealogy.schemas import (
    AddChildNodeRequest,
    AddMarriageRequest,
    DirectoryMemberResponse,
    DirectorySearchResponse,
    MemberCreateRequest,
    MemberResponse,
    MemberUpdateRequest,
)

# ... search_directory_service giữ nguyên ...


# ---------- Helper: dịch lỗi SQL Server ----------
_SQL_MSG_RE = re.compile(r"(?P<msg>.*?)\s*\((?P<num>\d+)\)", re.DOTALL)

# Tra theo nội dung thông báo của SP (không phân biệt hoa thường)
_KEYWORD_MESSAGES: list[tuple[str, str]] = [
    ("already married", "Hai người này đã là vợ chồng của nhau."),
    ("đã kết hôn", "Hai người này đã là vợ chồng của nhau."),
    ("cycle", "Quan hệ này tạo ra vòng lặp thế hệ trong cây gia phả."),
    ("circular", "Quan hệ này tạo ra vòng lặp thế hệ trong cây gia phả."),
    ("vòng lặp", "Quan hệ này tạo ra vòng lặp thế hệ trong cây gia phả."),
    ("not found", "Không tìm thấy thành viên được chỉ định."),
    ("không tồn tại", "Không tìm thấy thành viên được chỉ định."),
]


def _parse_sql_error(exc: DBAPIError) -> tuple[int | None, str]:
    """Tách (mã lỗi, nội dung) từ lỗi pyodbc của SQL Server."""
    raw = str(exc.orig) if exc.orig is not None else str(exc)
    tail = raw.rsplit("[SQL Server]", 1)[-1]
    match = _SQL_MSG_RE.search(tail)
    if match:
        return int(match.group("num")), match.group("msg").strip()
    return None, tail.strip()


def _translate_sql_error(exc: DBAPIError, default: str) -> str:
    """Trả về thông báo tiếng Việt an toàn để hiển thị cho người dùng."""
    number, message = _parse_sql_error(exc)
    lowered = message.lower()

    for keyword, vietnamese in _KEYWORD_MESSAGES:
        if keyword in lowered:
            return vietnamese

    # Lỗi do team tự THROW/RAISERROR trong SP (mã >= 50000): thông báo đã được
    # viết cho người dùng nên trả nguyên văn
    if number is not None and number >= 50000 and message:
        return message

    if number == 547:  # vi phạm khóa ngoại
        return "Dữ liệu tham chiếu không hợp lệ hoặc đang được sử dụng ở nơi khác."
    if number in (2601, 2627):  # trùng khóa duy nhất
        return "Dữ liệu này đã tồn tại trong hệ thống."

    return default


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _to_member_response(row: Any) -> MemberResponse:
    return MemberResponse.model_validate(dict(row))


# ---------- Member ----------
def create_member_service(db: Session, payload: MemberCreateRequest) -> MemberResponse:
    if payload.birth_date and payload.death_date and payload.death_date < payload.birth_date:
        raise _bad_request("Ngày mất không được trước ngày sinh.")

    try:
        row = repository.create_member(db, payload)
    except IntegrityError as exc:
        raise _bad_request(
            _translate_sql_error(exc, "Dòng họ hoặc chi được chọn không tồn tại.")
        ) from exc
    except SQLAlchemyError as exc:
        raise _bad_request(
            _translate_sql_error(exc, "Không thể tạo thành viên.")
            if isinstance(exc, DBAPIError)
            else "Không thể tạo thành viên."
        ) from exc
    return _to_member_response(row)


def