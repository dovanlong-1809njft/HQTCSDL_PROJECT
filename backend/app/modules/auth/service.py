from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, dummy_password_hash, hash_password, password_hash
from app.modules.auth.models import User
from app.modules.auth.schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse


def register_user(payload: RegisterRequest, db: Session) -> AuthResponse:
    email = str(payload.email).strip().lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=409, detail="Email này đã được đăng ký.")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role="member",
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email này đã được đăng ký.") from None
    db.refresh(user)
    return AuthResponse(access_token=create_access_token(user), user=UserResponse.model_validate(user))


def authenticate_user(payload: LoginRequest, db: Session) -> AuthResponse:
    email = str(payload.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        password_hash.verify(payload.password, dummy_password_hash)
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu chưa chính xác.", headers={"WWW-Authenticate": "Bearer"})

    if not user.is_active or not password_hash.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu chưa chính xác.", headers={"WWW-Authenticate": "Bearer"})

    return AuthResponse(access_token=create_access_token(user), user=UserResponse.model_validate(user))
