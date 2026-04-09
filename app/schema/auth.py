from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    login: str
    password: str


class RegisterAdminRequest(BaseModel):
    login: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class AdminMeResponse(BaseModel):
    id: int
    login: str
    name: str
    is_active: bool
    role: str = "admin"
