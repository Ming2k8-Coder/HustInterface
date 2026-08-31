from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class UserCredentials(BaseModel):
    email: str = Field(..., description="Email HUST (@sis.hust.edu.vn hoặc @hust.edu.vn)")
    password: str = Field(..., description="Mật khẩu tài khoản HUST")


class TokenInfo(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() >= self.expires_at


class ServiceSessionData(BaseModel):
    service_name: str
    is_authenticated: bool = False
    token: Optional[TokenInfo] = None
    cookies: Dict[str, str] = Field(default_factory=dict)
    headers: Dict[str, str] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
    student_id: Optional[str] = None
    student_name: Optional[str] = None


class SessionCache(BaseModel):
    ictsv: Optional[ServiceSessionData] = None
    ehust: Optional[ServiceSessionData] = None
    ctms: Optional[ServiceSessionData] = None
    last_saved: datetime = Field(default_factory=datetime.now)


class AuthStatusResponse(BaseModel):
    overall_authenticated: bool
    services: Dict[str, Dict[str, Any]]
    cached_session_path: str
