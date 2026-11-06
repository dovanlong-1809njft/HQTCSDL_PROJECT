from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select, true
from sqlalchemy.orm import Session

from app.core.config import ACCESS_TOKEN_MINUTES, ALGORITHM, JWT_SECRET_KEY
from app.core.database import get_db
from app.domains.identity.models import User

secret_key = JWT_SECRET_KEY
password_hash = PasswordHash.recommended()
dummy_password_hash = password_hash.hash("familyconnect-invalid-user-password")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(credentials.credentials, secret_key, algorithms=[ALGORITHM])
        user_id = UUID(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        raise unauthorized from None

    user = db.scalar(select(User).where(User.id == user_id, User.is_active == true()))
    if user is None:
        raise unauthorized
    return user
