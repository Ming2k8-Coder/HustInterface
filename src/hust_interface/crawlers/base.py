from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from loguru import logger

from ..config import settings
from ..core.session_manager import session_manager
from ..core.http_client import AsyncHustHttpClient
from ..models.auth_models import ServiceSessionData


class BaseCrawler(ABC):
    """
    Abstract base class for all HUST service crawlers.
    Handles HTTP client lifecycles, session injection, and standardized error handling.
    """

    def __init__(self, service_name: str, base_url: str):
        self.service_name = service_name
        self.base_url = base_url
        self._client: Optional[AsyncHustHttpClient] = None

    def get_session(self) -> Optional[ServiceSessionData]:
        return session_manager.get_service_session(self.service_name)

    def is_authenticated(self) -> bool:
        sess = self.get_session()
        if not sess or not sess.is_authenticated:
            return False
        if sess.token and sess.token.is_expired():
            return False
        return True

    def get_http_client(self) -> AsyncHustHttpClient:
        sess = self.get_session()
        headers = sess.headers if sess else {}
        cookies = sess.cookies if sess else {}

        return AsyncHustHttpClient(
            base_url=self.base_url,
            default_headers=headers,
            default_cookies=cookies,
            timeout=settings.HTTP_TIMEOUT_SECONDS
        )

    def require_auth(self) -> None:
        if not self.is_authenticated():
            raise PermissionError(
                f"Service '{self.service_name}' is not authenticated. "
                f"Please log in using SSO or provide valid token/cookie via configuration."
            )
