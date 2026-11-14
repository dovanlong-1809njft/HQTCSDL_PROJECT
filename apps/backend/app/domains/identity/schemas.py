from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, TypeAdapter, field_validator


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def existing_email(cls, value):
        if not isinstance(value, str):
            return value
        value = value.strip()
        # Existing SQL fixtures use reserved addresses; login still verifies the hash.
        if value.lower().endswith(".invalid"):
            return value
        return str(TypeAdapter(EmailStr).validate_python(value))


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
