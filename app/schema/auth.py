from pydantic import BaseModel, Field

from app.model import StaffRole


class StaffLoginRequest(BaseModel):
    login: str
    password: str


class CreateStaffRequest(BaseModel):
    login: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    role: StaffRole


class UpdateStaffRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: StaffRole | None = None
    is_active: bool | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: StaffRole


class StaffMeResponse(BaseModel):
    id: int
    login: str
    name: str
    role: StaffRole
    is_active: bool


class StaffResponse(BaseModel):
    id: int
    login: str
    name: str
    role: StaffRole
    is_active: bool
