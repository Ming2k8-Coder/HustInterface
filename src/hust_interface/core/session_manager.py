import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger

from ..config import settings
from ..models.auth_models import SessionCache, ServiceSessionData, TokenInfo


class SessionManager:
    """
    Manages session persistence, tokens, and cookies across HUST subservices.
    Stores and reads encrypted/JSON cache file locally to avoid repetitive SSO logins.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or settings.session_file_path
        self.cache = self._load_cache()

    def _load_cache(self) -> SessionCache:
        if not self.storage_path.exists():
            return SessionCache()
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return SessionCache.model_validate(data)
        except Exception as e:
            logger.warning(f"Failed to load cached session from {self.storage_path}: {e}")
            return SessionCache()

    def save_cache(self) -> None:
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache.last_saved = datetime.now()
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.cache.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
            logger.debug(f"Session saved successfully to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save session cache: {e}")

    def get_service_session(self, service_name: str) -> Optional[ServiceSessionData]:
        # Always reload from file if file exists to prevent stale cache in multi-process/test environments
        if self.storage_path.exists():
            try:
                self.cache = self._load_cache()
            except Exception:
                pass

        # Check explicit env override first
        if service_name == "ictsv" and settings.ICTSV_TOKEN:
            return ServiceSessionData(
                service_name="ictsv",
                is_authenticated=True,
                token=TokenInfo(access_token=settings.ICTSV_TOKEN),
                headers={"Authorization": f"Bearer {settings.ICTSV_TOKEN}"}
            )
        if service_name == "ehust" and settings.EHUST_SESSION_COOKIE:
            return ServiceSessionData(
                service_name="ehust",
                is_authenticated=True,
                cookies={"ASP.NET_SessionId": settings.EHUST_SESSION_COOKIE}
            )
        if service_name == "ctms" and settings.CTMS_SESSION_COOKIE:
            return ServiceSessionData(
                service_name="ctms",
                is_authenticated=True,
                cookies={"MoodleSession": settings.CTMS_SESSION_COOKIE}
            )

        # Fallback to local cached file
        return getattr(self.cache, service_name, None)

    def set_service_session(
        self,
        service_name: str,
        token: Optional[TokenInfo] = None,
        cookies: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        student_id: Optional[str] = None,
        student_name: Optional[str] = None
    ) -> ServiceSessionData:
        session = ServiceSessionData(
            service_name=service_name,
            is_authenticated=True,
            token=token,
            cookies=cookies or {},
            headers=headers or {},
            student_id=student_id,
            student_name=student_name,
            last_updated=datetime.now()
        )
        setattr(self.cache, service_name, session)
        self.save_cache()
        return session

    def clear_service_session(self, service_name: str) -> None:
        if hasattr(self.cache, service_name):
            setattr(self.cache, service_name, None)
            self.save_cache()

    def clear_all(self) -> None:
        self.cache = SessionCache()
        self.save_cache()

    def get_auth_summary(self) -> Dict[str, Any]:
        summary = {}
        for svc in ["ictsv", "ehust", "ctms"]:
            sess = self.get_service_session(svc)
            if sess and sess.is_authenticated:
                expired = sess.token.is_expired() if sess.token else False
                summary[svc] = {
                    "authenticated": not expired,
                    "student_id": sess.student_id,
                    "student_name": sess.student_name,
                    "last_updated": sess.last_updated.isoformat() if sess.last_updated else None,
                    "has_token": bool(sess.token),
                    "has_cookies": bool(sess.cookies),
                    "expired": expired
                }
            else:
                summary[svc] = {
                    "authenticated": False,
                    "status": "Not configured"
                }
        return summary


# Global session manager instance
session_manager = SessionManager()
