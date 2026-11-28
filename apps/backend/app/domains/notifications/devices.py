"""Đăng ký thiết bị nhận thông báo đẩy (Firebase Cloud Messaging).

App trên điện thoại xin token FCM rồi gọi POST /api/notifications/devices để
lưu token. Tiến trình nền đọc bảng community.DeviceTokens và gửi thông báo tới
từng thiết bị, nên điện thoại nhận được thông báo ngay cả khi app đang đóng.
"""
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.domains.heritage.repository import execute
from app.domains.identity.models import User

router = APIRouter(prefix="/notifications/devices", tags=["notifications"])
DB = Annotated[Session, Depends(get_db)]
Actor = Annotated[User, Depends(get_current_user)]


class DeviceTokenRequest(BaseModel):
    token: str = Field(min_length=10, max_length=400)
    platform: Literal["android", "ios", "web"] = "android"


@router.post("", status_code=204)
def register_device(payload: DeviceTokenRequest, db: DB, actor: Actor) -> None:
    """Lưu hoặc gia hạn token của thiết bị đang đăng nhập.

    Gọi lại nhiều lần với cùng token là bình thường: app nên gọi mỗi lần mở và
    mỗi lần FCM cấp token mới. Thủ tục dùng MERGE nên không sinh dòng trùng.
    """
    try:
        execute(
            db,
            "EXEC community.usp_UpsertDeviceToken @UserId=:user_id, @Token=:token, @Platform=:platform",
            dict(user_id=actor.id, token=payload.token.strip(), platform=payload.platform),
        ).close()
        db.commit()
    except DBAPIError:
        db.rollback()
        raise HTTPException(422, "Không lưu được thiết bị nhận thông báo.") from None


@router.delete("", status_code=204)
def unregister_device(payload: DeviceTokenRequest, db: DB, actor: Actor) -> None:
    """Gỡ token khi người dùng đăng xuất khỏi thiết bị đó."""
    try:
        execute(
            db,
            "EXEC community.usp_DeleteDeviceToken @Token=:token, @UserId=:user_id",
            dict(token=payload.token.strip(), user_id=actor.id),
        ).close()
        db.commit()
    except DBAPIError:
        db.rollback()
        raise HTTPException(422, "Không gỡ được thiết bị nhận thông báo.") from None
