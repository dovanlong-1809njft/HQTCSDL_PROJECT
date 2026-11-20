import re
from collections.abc import Callable
from typing import TypeVar
from uuid import UUID

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.domains.admin import repository
from app.domains.admin.schemas import (
    DEFAULT_SITE_SETTINGS,
    SITE_CONFIG_KEYS,
    SiteSettings,
    FamilyActivityResponse,
    PendingVerificationResponse,
    ReportedContentResponse,
    ResolveReportRequest,
    ResolveReportResponse,
    ReviewVerificationRequest,
    ReviewVerificationResponse,
    SystemConfigCreate,
    SystemConfigResponse,
    SystemConfigUpdate,
)

T = TypeVar("T")

# Mã THROW của các Procedure quản trị; không trả SQL/parameter thô ra API.
SQL_ERRORS = {
    51001: (422, "Quyết định xác minh không hợp lệ."),
    51002: (503, "Yêu cầu đang được xử lý. Vui lòng thử lại."),
    51003: (403, "Bạn không có quyền duyệt xác minh."),
    51004: (404, "Không tìm thấy yêu cầu xác minh."),
    51005: (409, "Yêu cầu xác minh đã được xử lý."),
    51006: (404, "Không tìm thấy hồ sơ thành viên."),
    51007: (403, "Trưởng chi không được tự duyệt yêu cầu của mình."),
    51008: (403, "Yêu cầu không thuộc chi bạn quản lý."),
    51009: (409, "Tài khoản cần xác minh đang bị khóa."),
    51010: (409, "Hồ sơ đã liên kết với tài khoản khác."),
    51011: (409, "Tài khoản đã liên kết với hồ sơ khác."),
    51030: (422, "Quyết định xử lý báo cáo không hợp lệ."),
    51031: (503, "Báo cáo đang được xử lý. Vui lòng thử lại."),
    51032: (403, "Chỉ admin được xử lý báo cáo."),
    51033: (404, "Không tìm thấy báo cáo."),
    51034: (409, "Báo cáo đã được xử lý."),
    51035: (404, "Nội dung bị báo cáo không còn tồn tại."),
    51036: (404, "Nội dung không còn tồn tại hoặc không phải ảnh được hỗ trợ."),
    51101: (422, "Dữ liệu cấu hình hoặc phân trang không hợp lệ."),
    51102: (403, "Bạn không có quyền thực hiện thao tác này."),
    51103: (409, "Khóa cấu hình đã tồn tại."),
    51104: (404, "Không tìm thấy cấu hình."),
    51201: (403, "Bạn không có quyền xem thống kê."),
    1205: (503, "Dữ liệu đang được xử lý. Vui lòng thử lại."),
    1222: (503, "Dữ liệu đang bị khóa. Vui lòng thử lại."),
}


def database_error(exc: DBAPIError) -> HTTPException:
    # Prefer the native code preserved by our T-SQL TRY/CATCH wrapper.
    # Only inspect the driver error, not SQLAlchemy's statement/parameter rendering.
    message = str(exc.orig)
    marker = re.search(r"\[FC_SQL:(\d+)\]", message)
    numbers = ([int(marker.group(1))] if marker
               else [int(code) for code in re.findall(r"\((\d{4,5})\)", message)])
    for number in numbers:
        if number in SQL_ERRORS:
            code, detail = SQL_ERRORS[number]
            return HTTPException(status_code=code, detail=detail)
    return HTTPException(status_code=500, detail="Không thể xử lý yêu cầu quản trị.")


def _execute(db: Session, operation: Callable[[], T], *, write: bool = False) -> T:
    try:
        result = operation()
        if write:
            # get_current_user đã mở transaction trên cùng Session trước khi gọi SP.
            db.commit()
        return result
    except DBAPIError as exc:
        db.rollback()
        raise database_error(exc) from None
    except Exception:
        if write:
            db.rollback()
        raise


def list_configs(db: Session, *, limit: int, offset: int) -> list[SystemConfigResponse]:
    return _execute(db, lambda: [SystemConfigResponse.model_validate(row)
                                for row in repository.list_configs(db, limit=limit, offset=offset)])


def get_site_settings(db: Session) -> SiteSettings:
    def operation():
        values = DEFAULT_SITE_SETTINGS.model_dump()
        for row in repository.get_site_configs(db):
            key = row["ConfigKey"].lower()
            if key in SITE_CONFIG_KEYS:
                values[SITE_CONFIG_KEYS[key][0]] = row["ConfigValue"]
        try:
            return SiteSettings.model_validate(values)
        except ValidationError:
            raise HTTPException(503, "Thiết lập website chưa hợp lệ. Vui lòng liên hệ quản trị viên.") from None
    return _execute(db, operation)


def save_site_settings(db: Session, payload: SiteSettings, actor_id: UUID) -> SiteSettings:
    def operation():
        existing = {row["ConfigKey"].lower() for row in repository.get_site_configs(db)}
        for key, (field, description) in SITE_CONFIG_KEYS.items():
            value = getattr(payload, field)
            value = str(value).lower() if isinstance(value, bool) else value
            write = repository.update_config if key in existing else repository.create_config
            write(db, actor_id=actor_id, config_key=key, config_value=value, description=description)
        return payload
    return _execute(db, operation, write=True)


def _checked_config_value(config_key: str, value: str) -> str:
    setting = SITE_CONFIG_KEYS.get(config_key.lower())
    if setting is None:
        return value
    field = setting[0]
    try:
        checked = SiteSettings.model_validate({**DEFAULT_SITE_SETTINGS.model_dump(), field: value})
    except ValidationError:
        raise HTTPException(422, "Giá trị thiết lập website không hợp lệ. Kiểm tra tên, URL logo, màu giao diện hoặc true/false cho đăng ký.") from None
    result = getattr(checked, field)
    return str(result).lower() if isinstance(result, bool) else result


def get_config(db: Session, config_key: str) -> SystemConfigResponse:
    def operation() -> SystemConfigResponse:
        row = repository.get_config(db, config_key)
        if row is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình.")
        return SystemConfigResponse.model_validate(row)
    return _execute(db, operation)


def create_config(db: Session, payload: SystemConfigCreate, actor_id: UUID) -> SystemConfigResponse:
    payload = payload.model_copy(update={"config_value": _checked_config_value(payload.config_key, payload.config_value)})
    return _execute(db, lambda: SystemConfigResponse.model_validate(repository.create_config(
        db, actor_id=actor_id, **payload.model_dump())), write=True)


def update_config(db: Session, config_key: str, payload: SystemConfigUpdate,
                  actor_id: UUID) -> SystemConfigResponse:
    payload = payload.model_copy(update={"config_value": _checked_config_value(config_key, payload.config_value)})
    return _execute(db, lambda: SystemConfigResponse.model_validate(repository.update_config(
        db, actor_id=actor_id, config_key=config_key, **payload.model_dump())), write=True)


def delete_config(db: Session, config_key: str, actor_id: UUID) -> None:
    _execute(db, lambda: repository.delete_config(db, actor_id=actor_id, config_key=config_key), write=True)


def list_pending_verifications(db: Session, reviewer_id: UUID, *, limit: int,
                               offset: int) -> list[PendingVerificationResponse]:
    return _execute(db, lambda: [PendingVerificationResponse.model_validate(row)
                                for row in repository.list_pending_verifications(
                                    db, reviewer_id=reviewer_id, limit=limit, offset=offset)])


def review_verification(db: Session, verification_id: UUID, payload: ReviewVerificationRequest,
                        reviewer_id: UUID) -> ReviewVerificationResponse:
    return _execute(db, lambda: ReviewVerificationResponse.model_validate(repository.review_verification(
        db, reviewer_id=reviewer_id, verification_id=verification_id, decision=payload.decision)), write=True)


def get_statistics(db: Session, actor_id: UUID) -> list[FamilyActivityResponse]:
    return _execute(db, lambda: [FamilyActivityResponse.model_validate(row)
                                for row in repository.get_statistics(db, actor_id)])


def list_reported_contents(db: Session, *, status: str, limit: int, offset: int) -> list[ReportedContentResponse]:
    return _execute(db, lambda: [ReportedContentResponse.model_validate(row)
                                for row in repository.list_reported_contents(db, status=status, limit=limit, offset=offset)])


def resolve_report(db: Session, report_id: UUID, payload: ResolveReportRequest,
                   reviewer_id: UUID) -> ResolveReportResponse:
    return _execute(db, lambda: ResolveReportResponse.model_validate(repository.resolve_report(
        db, report_id=report_id, reviewer_id=reviewer_id, decision=payload.decision)), write=True)
