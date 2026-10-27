"""
Haiox Bounty Hunter - Base Ingestion Driver
Module: ingestion/base.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import abc
import asyncio
import logging
from typing import List, Optional, Any, Dict
import httpx

from core.schemas import RawJobPosting, PlatformType, FeedConfig

logger = logging.getLogger("bounty_hunter.ingestion")


class BaseFeedDriver(abc.ABC):
    """Abstract base class for all platform ingestion drivers."""

    def __init__(self, platform: PlatformType, config: Optional[FeedConfig] = None):
        self.platform = platform
        self.config = config or FeedConfig()
        self.last_fetch_timestamp: float = 0.0

    @abc.abstractmethod
    async def fetch_jobs(self) -> List[RawJobPosting]:
        """Asynchronously fetches and parses the latest jobs from the platform."""
        pass

    @abc.abstractmethod
    def parse_payload(self, raw_data: Any) -> List[RawJobPosting]:
        """Parses raw API/feed response into standardized RawJobPosting objects."""
        pass

    async def _safe_http_get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[httpx.Response]:
        """Executes resilient HTTP GET request with timeouts and standard headers."""
        req_headers = {"User-Agent": self.config.user_agent}
        if headers:
            req_headers.update(headers)

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds, follow_redirects=True) as client:
                resp = await client.get(url, params=params, headers=req_headers)
                if resp.status_code == 200:
                    return resp
                else:
                    logger.warning(f"[{self.platform.value}] HTTP {resp.status_code} from {url}")
                    return None
        except httpx.TimeoutException:
            logger.warning(f"[{self.platform.value}] Request timed out to {url}")
            return None
        except Exception as exc:
            logger.error(f"[{self.platform.value}] Network error for {url}: {exc}")
            return None
