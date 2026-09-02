from typing import Optional, Dict, Any
from datetime import datetime
import jwt
from loguru import logger

from ..core.session_manager import session_manager
from ..models.auth_models import ServiceSessionData, TokenInfo


class ManualAuthenticator:
    """
    Handles direct input of tokens, cookies, and API keys.
    Extracts student info from JWT tokens when possible.
    """

    @staticmethod
    def set_ictsv_token(token_str: str) -> ServiceSessionData:
        clean_token = token_str.replace("Bearer ", "").strip()
        student_id = None
        student_name = None
        expires_at = None

        # Decode JWT claims if valid JWT format
        try:
            unverified_claims = jwt.decode(clean_token, options={"verify_signature": False})
            student_id = (
                unverified_claims.get("user_name")
                or unverified_claims.get("username")
                or unverified_claims.get("student_id")
                or unverified_claims.get("sub")
            )
            student_name = unverified_claims.get("name") or unverified_claims.get("full_name")
            if "exp" in unverified_claims:
                expires_at = datetime.fromtimestamp(unverified_claims["exp"])
        except Exception as e:
            logger.debug(f"Could not parse JWT claims from iCTSV token: {e}")

        token_info = TokenInfo(
            access_token=clean_token,
            token_type="Bearer",
            expires_at=expires_at
        )

        return session_manager.set_service_session(
            service_name="ictsv",
            token=token_info,
            headers={"Authorization": f"Bearer {clean_token}"},
            student_id=student_id,
            student_name=student_name
        )

    @staticmethod
    def set_ehust_cookie(cookie_str: str, student_id: Optional[str] = None) -> ServiceSessionData:
        cookies_dict: Dict[str, str] = {}
        # Parse cookie string if raw header string or document.cookie provided
        if "=" in cookie_str and ";" in cookie_str:
            for item in cookie_str.split(";"):
                if "=" in item:
                    k, v = item.strip().split("=", 1)
                    cookies_dict[k] = v
        elif "=" in cookie_str:
            k, v = cookie_str.strip().split("=", 1)
            cookies_dict[k] = v
        else:
            # If plain token string passed, map to x-access-token
            cookies_dict["x-access-token"] = cookie_str.strip()
            cookies_dict["token"] = cookie_str.strip()

        # If x-access-token or token is present, check JWT payload for student ID
        resolved_sid = student_id
        resolved_name = None
        main_tok = cookies_dict.get("x-access-token") or cookies_dict.get("token")
        if main_tok:
            try:
                claims = jwt.decode(main_tok, options={"verify_signature": False})
                if not resolved_sid:
                    resolved_sid = claims.get("student_id") or claims.get("sub") or claims.get("email")
                resolved_name = claims.get("name") or claims.get("fullName")
            except Exception:
                pass

        return session_manager.set_service_session(
            service_name="ehust",
            cookies=cookies_dict,
            student_id=resolved_sid,
            student_name=resolved_name
        )


    @staticmethod
    def set_ctms_cookie(cookie_str: str, student_id: Optional[str] = None) -> ServiceSessionData:
        cookies_dict: Dict[str, str] = {}
        if "=" in cookie_str:
            k, v = cookie_str.strip().split("=", 1)
            cookies_dict[k] = v
        else:
            cookies_dict["MoodleSession"] = cookie_str.strip()

        return session_manager.set_service_session(
            service_name="ctms",
            cookies=cookies_dict,
            student_id=student_id
        )
