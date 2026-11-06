from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    FAMILY_HEAD = "family_head"
    MEMBER = "member"
    GUEST = "guest"
