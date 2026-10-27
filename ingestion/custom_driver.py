"""
Haiox Project Scout - Custom User-Defined Site Ingestion Driver
Module: ingestion/custom_driver.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import time
import logging
import re
from typing import List, Dict, Any, Optional

from core.schemas import RawJobPosting, PlatformType, CustomSiteSpec, FeedConfig
from .base import BaseFeedDriver
from .upwork_driver import UpworkFeedDriver

logger = logging.getLogger("project_scout.custom_driver")


class CustomSiteDriver(BaseFeedDriver):
    """
    User-extensible driver that enables adding any custom platform,
    RSS channel, or JSON API endpoint into the Scout pipeline.
    """

    def __init__(self, spec: CustomSiteSpec, config: Optional[FeedConfig] = None):
        super().__init__(PlatformType.CUSTOM, config)
        self.spec = spec

    async def fetch_jobs(self) -> List[RawJobPosting]:
        resp = await self._safe_http_get(self.spec.feed_url, headers=self.spec.headers)
        if not resp:
            return []

        try:
            if self.spec.feed_type.lower() == "rss" or "<rss" in resp.text:
                # Use robust RSS parser
                up_parser = UpworkFeedDriver(self.config)
                raw_items = up_parser.parse_payload(resp.text)
                for item in raw_items:
                    item.platform = PlatformType.CUSTOM
                    item.custom_platform_name = self.spec.name
                    item.id = f"custom_{self.spec.name}_{item.id}"
                return raw_items
            else:
                return self.parse_payload(resp.json())
        except Exception as e:
            logger.error(f"[CustomSite:{self.spec.name}] Failed to parse payload: {e}")
            return []

    def parse_payload(self, raw_data: Any) -> List[RawJobPosting]:
        items: List[RawJobPosting] = []
        if isinstance(raw_data, dict):
            raw_list = raw_data.get("jobs", []) or raw_data.get("items", []) or raw_data.get("posts", [])
        elif isinstance(raw_data, list):
            raw_list = raw_data
        else:
            return items

        for it in raw_list:
            if not isinstance(it, dict):
                continue

            try:
                raw_id = str(it.get("id") or hash(str(it)))[-8:]
                title = str(it.get("title", "")).strip()
                description = str(it.get("description", "") or it.get("summary", "")).strip()
                if not title:
                    continue

                b_min = float(it.get("budget_min", 0.0) or it.get("price", 0.0) or 0.0)
                b_max = float(it.get("budget_max", 0.0) or it.get("budget", 0.0) or b_min)
                currency = str(it.get("currency", "USD")).upper()

                job = RawJobPosting(
                    id=f"cst_{self.spec.name}_{raw_id}",
                    platform=PlatformType.CUSTOM,
                    custom_platform_name=self.spec.name,
                    title=title,
                    description=description,
                    budget_min=b_min,
                    budget_max=b_max,
                    currency=currency,
                    client_spend=float(it.get("client_spend", 0.0) or 0.0),
                    client_rating=float(it.get("client_rating", 5.0) or 5.0),
                    payment_verified=bool(it.get("payment_verified", True)),
                    skills=it.get("skills", []),
                    published_at=float(it.get("published_at", time.time())),
                    source_url=str(it.get("url", self.spec.feed_url)),
                    raw_metadata=it
                )
                items.append(job)
            except Exception as e:
                logger.debug(f"[CustomSite:{self.spec.name}] Skipping malformed item: {e}")
                continue

        return items
