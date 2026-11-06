from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.identity.models import User


def require_role(*allowed_roles: str) -> Callable[[User], User]:
    """Dependency kiểm tra quyền RBAC (ví dụ: admin, family_head, member)."""

    def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if allowed_roles and current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền thực hiện thao tác này.",
            )
        return current_user

    return role_checker


__all__ = ["get_current_user", "get_db", "require_role"]
