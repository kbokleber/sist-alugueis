from pydantic import BaseModel, EmailStr, ConfigDict


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str
    email: Optional[str] = None
    is_superuser: bool = False
    type: str
    exp: int
    iat: int
    jti: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    user_id: str | None = None
