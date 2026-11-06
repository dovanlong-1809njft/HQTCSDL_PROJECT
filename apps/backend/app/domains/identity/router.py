from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.domains.identity.models import User
from app.domains.identity.schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.domains.identity.services import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> AuthResponse:
    return register_user(payload, db)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> AuthResponse:
    return authenticate_user(payload, db)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.model_validate(current_user)
