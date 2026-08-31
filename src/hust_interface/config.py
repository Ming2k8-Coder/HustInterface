from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # User Credentials
    HUST_EMAIL: Optional[str] = Field(default=None, description="HUST Student Email (ví dụ: minh.nt2611037@sis.hust.edu.vn)")
    HUST_PASSWORD: Optional[str] = Field(default=None, description="HUST Student Password")

    # Tokens / Cookies override
    ICTSV_TOKEN: Optional[str] = Field(default=None, description="Direct TokenCode / Bearer token for CTSV API")
    EHUST_SESSION_COOKIE: Optional[str] = Field(default=None, description="Session cookie for eHUST (JSESSIONID / ASP.NET_SessionId)")
    CTMS_SESSION_COOKIE: Optional[str] = Field(default=None, description="Session cookie for CTMS (MoodleSession)")

    # Base URLs (Direct HUST domains)
    CTSV_BASE_URL: str = Field(default="https://ctsv.hust.edu.vn", description="Base URL for CTSV portal")
    CTSV_LOGIN_URL: str = Field(default="https://ctsv.hust.edu.vn/#/login", description="Direct CTSV login page")
    CTSV_API_BASE_URL: str = Field(default="https://ctsv.hust.edu.vn/api-t", description="Direct CTSV API endpoint")

    EHUST_BASE_URL: str = Field(default="https://e.hust.edu.vn", description="Base URL for eHUST portal")
    EHUST_SSO_LOGIN_URL: str = Field(default="https://e.hust.edu.vn/sso/login", description="Direct eHUST SSO login URL")
    QLDT_BASE_URL: str = Field(default="https://qldt.hust.edu.vn", description="Base URL for QLĐT portal")
    CTMS_BASE_URL: str = Field(default="https://ctms.hust.edu.vn", description="Base URL for CTMS portal")

    # Storage Paths
    SESSION_STORAGE_DIR: Path = Field(
        default_factory=lambda: Path.home() / ".hust_interface",
        description="Directory to cache session tokens and cookies securely"
    )
    SESSION_FILE_NAME: str = "session_cache.json"

    # Performance & HTTP Settings
    HTTP_TIMEOUT_SECONDS: float = Field(default=15.0, description="HTTP Request Timeout in seconds")
    MAX_RETRIES: int = Field(default=3, description="Maximum retry count for transient network failures")
    USER_AGENT: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        description="Default realistic browser User-Agent"
    )
    HEADLESS_BROWSER: bool = Field(default=True, description="Run browser automation in headless mode")

    # MCP Server Configuration
    MCP_SERVER_NAME: str = "hust-interface"
    MCP_SERVER_VERSION: str = "0.1.0"
    MCP_HOST: str = "127.0.0.1"
    MCP_PORT: int = 8000

    @property
    def session_file_path(self) -> Path:
        self.SESSION_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        return self.SESSION_STORAGE_DIR / self.SESSION_FILE_NAME


# Global settings instance
settings = Settings()
