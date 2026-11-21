from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(default="student", pattern="^(student|professor|admin)$")
    locale: str = Field(default="en")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ConsentFlags(BaseModel):
    audio_retention: bool = True
    analytics_sharing: bool = True
    professor_sharing: bool = True


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    institution_id: Optional[str] = None
    locale: str
    consent_flags: Dict[str, Any]

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserResponse
    message: str
    token_type: str = "bearer"
