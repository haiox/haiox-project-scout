"""
Haiox Bounty Hunter - Local Market Ingestion Driver
Module: ingestion/local_driver.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import time
import logging
from typing import List, Dict, Any, Optional

from core.schemas import RawJobPosting, PlatformType, FeedConfig
from .base import BaseFeedDriver

logger = logging.getLogger("bounty_hunter.local")


class LocalFeedDriver(BaseFeedDriver):
    """Driver for extracting immediate cash Python/scraping gigs from domestic developer boards."""

    FEED_ENDPOINT = "https://api.haiox.local/feeds/python"

    def __init__(self, config: Optional[FeedConfig] = None):
        super().__init__(PlatformType.LOCAL, config)

    async def fetch_jobs(self) -> List[RawJobPosting]:
        # Fast guard: skip unresolvable mock local domain to avoid DNS wait
        if ".local" in self.FEED_ENDPOINT:
            return []
        resp = await self._safe_http_get(self.FEED_ENDPOINT)
        if not resp:
            return []

        try:
            return self.parse_payload(resp.json())
        except Exception as e:
            logger.error(f"[LocalDriver] Failed to parse local payload: {e}")
            return []

    def parse_payload(self, raw_data: Any) -> List[RawJobPosting]:
        items: List[RawJobPosting] = []
        if not isinstance(raw_data, (list, dict)):
            return items

        projects = raw_data.get("projects", []) if isinstance(raw_data, dict) else raw_data

        for p in projects:
            if not isinstance(p, dict):
                continue

            try:
                p_id = str(p.get("id", hash(str(p))))[-8:]
                title = str(p.get("title", "")).strip()
                description = str(p.get("description", "")).strip()
                if not title:
                    continue

                b_min = float(p.get("budget_min", 0.0) or 0.0)
                b_max = float(p.get("budget_max", 0.0) or b_min)
                currency = str(p.get("currency", "TOMAN")).upper()

                verified = bool(p.get("is_verified", True))
                spend = float(p.get("client_total_spent", 0.0) or 0.0)
                rating = float(p.get("client_rating", 5.0) or 5.0)
                skills = p.get("skills", ["Python", "Web Scraping"])

                job = RawJobPosting(
                    id=f"loc_{p_id}",
                    platform=PlatformType.LOCAL,
                    title=title,
                    description=description,
                    budget_min=b_min,
                    budget_max=b_max,
                    currency=currency,
                    client_spend=spend,
                    client_rating=rating,
                    payment_verified=verified,
                    skills=skills,
                    published_at=float(p.get("created_at", time.time())),
                    raw_metadata=p
                )
                items.append(job)
            except Exception as err:
                logger.debug(f"[LocalDriver] Skipping item: {err}")
                continue

        return items
