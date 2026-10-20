from pydantic import BaseModel, ConfigDict

from vinichannels.domain.identity.entities import Role


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    role: Role
    is_active: bool


class UserCreateRequest(BaseModel):
    email: str
    password: str
    role: Role


class UserUpdateRequest(BaseModel):
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
