import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from loguru import logger

from ..config import settings
from ..core.http_client import AsyncHustHttpClient
from ..core.session_manager import session_manager
from .manual_auth import ManualAuthenticator


class DirectHttpAuthenticator:
    """
    Direct HTTP Authenticator for HUST services.
    Targets:
    1. eHUST: https://e.hust.edu.vn/sso/login (Direct form POST)
    2. CTSV: https://ctsv.hust.edu.vn/api-t/User/UserLogin (Direct API POST)
    Completely avoids Microsoft SSO / Azure AD redirects.
    """

    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        self.email = email or settings.HUST_EMAIL
        self.password = password or settings.HUST_PASSWORD

    async def login_ehust_http(self) -> bool:
        """
        Direct HTTP login to eHUST via https://e.hust.edu.vn/sso/login.
        Extracts JSESSIONID and session cookies directly without browser.
        """
        if not self.email or not self.password:
            logger.error("Email and password are required for eHUST login.")
            return False

        logger.info(f"Logging in directly to eHUST ({settings.EHUST_SSO_LOGIN_URL}) for {self.email}...")

        async with AsyncHustHttpClient() as client:
            try:
                # Step 1: Initial GET to initialize session cookie
                get_res = await client.get(settings.EHUST_SSO_LOGIN_URL)
                
                # Step 2: Form POST
                post_payload = {
                    "username": self.email,
                    "password": self.password
                }
                post_res = await client.post(
                    settings.EHUST_SSO_LOGIN_URL,
                    data=post_payload
                )

                # Capture cookies from client jar
                cookies_dict = dict(client.client.cookies)
                logger.debug(f"eHUST login response status: {post_res.status_code}, cookies: {list(cookies_dict.keys())}")

                if "JSESSIONID" in cookies_dict or post_res.status_code in [200, 302]:
                    # Extract student_id from email prefix (e.g. minh.nt2611037 -> 202611037, or 20210001 -> 20210001)
                    student_id = None
                    digits_match = re.search(r"(\d{6,9})", self.email)
                    if digits_match:
                        raw_digits = digits_match.group(1)
                        if len(raw_digits) == 7 and raw_digits.startswith("26"):
                            student_id = f"20{raw_digits}"  # 2611037 -> 202611037 (K69 HUST standard MSSV format)
                        elif len(raw_digits) == 7 and int(raw_digits[:2]) in range(15, 30):
                            student_id = f"20{raw_digits}"
                        else:
                            student_id = raw_digits

                    session_manager.set_service_session(
                        service_name="ehust",
                        cookies=cookies_dict,
                        student_id=student_id
                    )

                    logger.info("Successfully logged in to eHUST via direct HTTP.")
                    return True
                else:
                    logger.warning("eHUST login did not return expected session cookies.")
                    return False

            except Exception as e:
                logger.error(f"Error during direct eHUST login: {e}")
                return False

    async def login_ictsv_http(self, captcha: Optional[str] = "") -> Dict[str, Any]:
        """
        Direct HTTP login to CTSV via https://ctsv.hust.edu.vn/api-t/User/UserLogin.
        """
        if not self.email or not self.password:
            return {"success": False, "message": "Email và mật khẩu không được để trống."}

        # Format username: CTSV accepts either student email or student ID / username
        username = self.email.split("@")[0] if "@" in self.email else self.email

        logger.info(f"Logging in directly to CTSV ({settings.CTSV_API_BASE_URL}/User/UserLogin) for {username}...")

        async with AsyncHustHttpClient(base_url=settings.CTSV_API_BASE_URL) as client:
            try:
                payload = {
                    "UserName": username,
                    "Password": self.password,
                    "Captcha": captcha or ""
                }
                res = await client.post("/User/UserLogin", json_data=payload)
                data = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}

                resp_code = data.get("RespCode")
                token_code = data.get("TokenCode")

                if resp_code == 0 and token_code:
                    ManualAuthenticator.set_ictsv_token(token_code)
                    session = session_manager.get_service_session("ictsv")
                    if session:
                        session.student_id = data.get("UserName", username)
                        session.student_name = data.get("FullName", "")
                        session_manager.save_cache()
                    logger.info(f"Successfully logged in to CTSV. Student: {data.get('FullName')}")
                    return {"success": True, "token": token_code, "user": data}
                else:
                    msg = data.get("RespText", f"Mã lỗi {resp_code}")
                    logger.warning(f"CTSV direct login failed: {msg}")
                    return {"success": False, "message": msg, "response": data}

            except Exception as e:
                logger.error(f"CTSV direct HTTP login exception: {e}")
                return {"success": False, "message": str(e)}

    async def login_all_direct(self) -> Dict[str, Any]:
        """
        Runs direct HTTP login for both eHUST and CTSV.
        """
        ehust_ok = await self.login_ehust_http()
        ictsv_result = await self.login_ictsv_http()

        return {
            "ehust": {"success": ehust_ok},
            "ictsv": ictsv_result
        }
