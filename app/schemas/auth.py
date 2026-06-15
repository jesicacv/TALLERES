from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    nombre_completo: str
    activo: bool
    debe_cambiar_password: bool


class AuthUserResponse(BaseModel):
    usuario: UserInfo
    roles: list[str]


class LogoutResponse(BaseModel):
    message: str
