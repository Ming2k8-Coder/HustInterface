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

    async def auto_reauthenticate(self) -> bool:
        """
        Attempts automatic re-authentication if credentials are provided in settings or environment.
        """
        if settings.HUST_EMAIL and settings.HUST_PASSWORD:
            logger.info(f"Auto-reauthenticating service '{self.service_name}' for {settings.HUST_EMAIL}...")
            try:
                from ..auth.direct_http_auth import DirectHttpAuthenticator
                auth = DirectHttpAuthenticator(email=settings.HUST_EMAIL, password=settings.HUST_PASSWORD)
                if self.service_name in ["ehust", "qldt"]:
                    return await auth.login_ehust_http()
                elif self.service_name == "ictsv":
                    res = await auth.login_ictsv_http()
                    return res.get("success", False)
            except Exception as e:
                logger.warning(f"Auto-reauthentication direct HTTP failed: {e}")
                
            # Fallback to browser-based direct login
            try:
                from ..auth.sso_authenticator import HustDirectAuthenticator
                direct_auth = HustDirectAuthenticator(
                    email=settings.HUST_EMAIL,
                    password=settings.HUST_PASSWORD,
                    headless=settings.HEADLESS_BROWSER
                )
                if self.service_name in ["ehust", "qldt"]:
                    return await direct_auth.login_ehust()
                elif self.service_name == "ictsv":
                    return await direct_auth.login_ctsv()
            except Exception as e:
                logger.error(f"Auto-reauthentication browser fallback failed: {e}")

        return False

    def require_auth(self) -> None:
        """
        Sync check for authentication status.
        """
        if not self.is_authenticated():
            raise PermissionError(
                f"Service '{self.service_name}' is not authenticated (or session expired). "
                f"Please log in or configure tokens."
            )

    async def ensure_authenticated(self) -> None:
        """
        Ensures the crawler is authenticated. If not authenticated or expired,
        triggers automatic re-authentication before raising an error.
        """
        if not self.is_authenticated():
            success = await self.auto_reauthenticate()
            if not success and not self.is_authenticated():
                raise PermissionError(
                    f"Service '{self.service_name}' is not authenticated (or session expired). "
                    f"Please provide HUST_EMAIL and HUST_PASSWORD in your environment or use 'hust_set_token' / 'hust_login_sso'."
                )


