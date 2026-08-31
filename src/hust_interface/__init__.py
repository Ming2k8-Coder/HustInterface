"""
HUST Interface: High-Performance Model Context Protocol (MCP) Server & Crawler
for Hanoi University of Science and Technology (HUST) Services.
"""

from .config import settings
from .core.session_manager import session_manager
from .core.http_client import AsyncHustHttpClient
from .server import mcp_server, create_mcp_server
from .crawlers import (
    BaseCrawler,
    IctsvCrawler,
    EhustCrawler,
    CtmsCrawler,
)

__version__ = "0.1.0"

__all__ = [
    "settings",
    "session_manager",
    "AsyncHustHttpClient",
    "mcp_server",
    "create_mcp_server",
    "BaseCrawler",
    "IctsvCrawler",
    "EhustCrawler",
    "CtmsCrawler",
]
