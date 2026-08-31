import asyncio
import json
from typing import Optional, Dict, Any
from loguru import logger
from playwright.async_api import async_playwright

from ..config import settings
from ..core.session_manager import session_manager
from .manual_auth import ManualAuthenticator


class HustDirectAuthenticator:
    """
    Automated browser login targeting direct HUST login forms:
    - CTSV: https://ctsv.hust.edu.vn/#/login
    - eHUST: https://e.hust.edu.vn/sso/login
    Completely avoids Microsoft SSO / Azure AD redirects.
    """

    def __init__(self, email: Optional[str] = None, password: Optional[str] = None, headless: bool = True):
        self.email = email or settings.HUST_EMAIL
        self.password = password or settings.HUST_PASSWORD
        self.headless = headless if headless is not None else settings.HEADLESS_BROWSER

    async def login_ctsv(self) -> bool:
        """
        Log in to CTSV portal at https://ctsv.hust.edu.vn/#/login and capture the TokenCode / JWT.
        """
        if not self.email or not self.password:
            raise ValueError("Email/Username và mật khẩu không được để trống.")

        username = self.email.split("@")[0] if "@" in self.email else self.email
        logger.info(f"Starting direct browser login for CTSV ({settings.CTSV_LOGIN_URL})...")
        captured_token: Optional[str] = None
        captured_name: Optional[str] = None

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(user_agent=settings.USER_AGENT)
            page = await context.new_page()

            # Intercept response of /User/UserLogin API
            async def handle_response(response):
                nonlocal captured_token, captured_name
                try:
                    if "User/UserLogin" in response.url:
                        res_json = await response.json()
                        if res_json.get("RespCode") == 0 and res_json.get("TokenCode"):
                            captured_token = res_json.get("TokenCode")
                            captured_name = res_json.get("FullName")
                            logger.info(f"Captured CTSV TokenCode: {captured_token[:15]}...")
                except Exception:
                    pass

            page.on("response", handle_response)

            try:
                await page.goto(settings.CTSV_LOGIN_URL, wait_until="networkidle", timeout=30000)

                # Fill username and password on the Vue CTSV form
                user_input = page.locator('input[placeholder*="tài khoản"], input[placeholder*="MSSV"], input[placeholder*="Email"], input[type="text"]').first
                pass_input = page.locator('input[placeholder*="mật khẩu"], input[type="password"]').first

                if await user_input.count() > 0:
                    await user_input.fill(username)
                if await pass_input.count() > 0:
                    await pass_input.fill(self.password)

                # Click Login Button
                login_btn = page.locator('button:has-text("Đăng nhập"), button[type="submit"]').first
                if await login_btn.count() > 0:
                    await login_btn.click()

                # Wait for navigation or token response
                await page.wait_for_timeout(4000)

                # Fallback: Read token from localStorage
                if not captured_token:
                    storage = await page.evaluate("() => ({ ...localStorage })")
                    for k, v in storage.items():
                        if "token" in k.lower():
                            captured_token = v.strip('"')
                            break

                if captured_token:
                    ManualAuthenticator.set_ictsv_token(captured_token)
                    session = session_manager.get_service_session("ictsv")
                    if session:
                        session.student_id = username
                        if captured_name:
                            session.student_name = captured_name
                        session_manager.save_cache()
                    logger.info("Successfully logged in to CTSV.")
                    return True
                else:
                    logger.warning("Could not capture TokenCode from CTSV login. Captcha may have blocked.")
                    return False

            except Exception as e:
                logger.error(f"Error during CTSV login: {e}")
                return False
            finally:
                await context.close()
                await browser.close()

    async def login_ehust(self) -> bool:
        """
        Log in to eHUST at https://e.hust.edu.vn/sso/login and capture session cookies.
        """
        if not self.email or not self.password:
            raise ValueError("Email và mật khẩu không được để trống.")

        logger.info(f"Starting direct browser login for eHUST ({settings.EHUST_SSO_LOGIN_URL})...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(user_agent=settings.USER_AGENT)
            page = await context.new_page()

            try:
                await page.goto(settings.EHUST_SSO_LOGIN_URL, wait_until="networkidle", timeout=30000)

                user_input = page.locator('input[name="username"]').first
                pass_input = page.locator('input[name="password"]').first

                if await user_input.count() > 0:
                    await user_input.fill(self.email)
                if await pass_input.count() > 0:
                    await pass_input.fill(self.password)

                submit_btn = page.locator('button[type="submit"], input[type="submit"]').first
                if await submit_btn.count() > 0:
                    await submit_btn.click()

                await page.wait_for_timeout(3000)

                # Capture cookies
                cookies = await context.cookies()
                cookie_dict = {c["name"]: c["value"] for c in cookies}

                if cookie_dict:
                    session_manager.set_service_session(
                        service_name="ehust",
                        cookies=cookie_dict,
                        student_id=self.email
                    )
                    logger.info("Successfully logged in to eHUST.")
                    return True
                return False

            except Exception as e:
                logger.error(f"Error during eHUST login: {e}")
                return False
            finally:
                await context.close()
                await browser.close()

    async def login_all(self) -> Dict[str, bool]:
        """
        Logs in to both CTSV and eHUST directly.
        """
        results = {}
        try:
            results["ctsv"] = await self.login_ctsv()
        except Exception as e:
            logger.error(f"CTSV login failed: {e}")
            results["ctsv"] = False

        try:
            results["ehust"] = await self.login_ehust()
        except Exception as e:
            logger.error(f"eHUST login failed: {e}")
            results["ehust"] = False

        return results


# Alias for backward compatibility
HustSSOAuthenticator = HustDirectAuthenticator
