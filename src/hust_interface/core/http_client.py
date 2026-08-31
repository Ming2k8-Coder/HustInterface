import asyncio
from typing import Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup
from loguru import logger

from ..config import settings


class AsyncHustHttpClient:
    """
    High-performance async HTTP client tailored for HUST educational services.
    Features:
    - HTTP/2 multiplexing & connection pooling
    - Cookie jar preservation
    - Automatic exponential backoff retries for transient connection drops
    - Fast HTML/JSON parsing helpers
    """

    def __init__(
        self,
        base_url: str = "",
        default_headers: Optional[Dict[str, str]] = None,
        default_cookies: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ):
        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua": '"Not A(Brand";v="8", "Chromium";v="133", "Google Chrome";v="133"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        if default_headers:
            headers.update(default_headers)

        try:
            self.client = httpx.AsyncClient(
                base_url=base_url,
                headers=headers,
                cookies=default_cookies or {},
                timeout=httpx.Timeout(timeout or settings.HTTP_TIMEOUT_SECONDS),
                http2=True,
                follow_redirects=True,
                verify=True
            )
        except ImportError:
            self.client = httpx.AsyncClient(
                base_url=base_url,
                headers=headers,
                cookies=default_cookies or {},
                timeout=httpx.Timeout(timeout or settings.HTTP_TIMEOUT_SECONDS),
                http2=False,
                follow_redirects=True,
                verify=True
            )

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: int = 3
    ) -> httpx.Response:
        for attempt in range(retries):
            try:
                response = await self.client.get(url, params=params, headers=headers)
                return response
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as e:
                if attempt == retries - 1:
                    logger.error(f"HTTP GET failed after {retries} attempts: {url} - {e}")
                    raise
                backoff = 0.5 * (2 ** attempt)
                logger.warning(f"HTTP GET failed ({e}), retrying in {backoff:.1f}s... [{attempt + 1}/{retries}]")
                await asyncio.sleep(backoff)

    async def post(
        self,
        url: str,
        data: Optional[Any] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: int = 3
    ) -> httpx.Response:
        for attempt in range(retries):
            try:
                response = await self.client.post(url, data=data, json=json_data, headers=headers)
                return response
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as e:
                if attempt == retries - 1:
                    logger.error(f"HTTP POST failed after {retries} attempts: {url} - {e}")
                    raise
                backoff = 0.5 * (2 ** attempt)
                logger.warning(f"HTTP POST failed ({e}), retrying in {backoff:.1f}s... [{attempt + 1}/{retries}]")
                await asyncio.sleep(backoff)

    async def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Any:
        response = await self.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    async def get_soup(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> BeautifulSoup:
        response = await self.get(url, params=params, headers=headers)
        response.raise_for_status()
        # lxml parser is faster than standard html.parser
        return BeautifulSoup(response.text, "lxml")

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
