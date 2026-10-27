"""
Haiox Bounty Hunter - Upwork Ingestion Driver
Module: ingestion/upwork_driver.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import re
import time
import logging
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET

from core.schemas import RawJobPosting, PlatformType, FeedConfig
from .base import BaseFeedDriver

logger = logging.getLogger("bounty_hunter.upwork")


class UpworkFeedDriver(BaseFeedDriver):
    """Driver for extracting targeted Python/AI/Scraping opportunities from Upwork RSS feeds."""

    FEED_URL = "https://www.upwork.com/ab/feed/jobs/rss"

    def __init__(self, config: Optional[FeedConfig] = None):
        super().__init__(PlatformType.UPWORK, config)

    async def fetch_jobs(self) -> List[RawJobPosting]:
        params = {
            "q": "python scraping automation",
            "sort": "recency",
            "paging": f"0;{self.config.max_items_per_pull}"
        }
        resp = await self._safe_http_get(self.FEED_URL, params=params)
        if not resp:
            return []

        return self.parse_payload(resp.text)

    def parse_payload(self, raw_data: Any) -> List[RawJobPosting]:
        items: List[RawJobPosting] = []
        if not raw_data:
            return items

        # Case 1: XML / RSS text string
        if isinstance(raw_data, str) and ("<rss" in raw_data or "<feed" in raw_data or "<item>" in raw_data):
            try:
                root = ET.fromstring(raw_data)
                channel = root.find("channel")
                raw_items = channel.findall("item") if channel is not None else root.findall(".//item")

                for it in raw_items:
                    job = self._parse_xml_item(it)
                    if job:
                        items.append(job)
            except Exception as e:
                logger.error(f"[Upwork] Error parsing RSS XML: {e}")
                return items
        # Case 2: JSON mock / API payload
        elif isinstance(raw_data, dict):
            raw_list = raw_data.get("jobs", []) or raw_data.get("items", [])
            for it in raw_list:
                job = self._parse_json_item(it)
                if job:
                    items.append(job)

        return items

    def _parse_xml_item(self, item_elem: ET.Element) -> Optional[RawJobPosting]:
        title = (item_elem.findtext("title") or "").strip()
        link = (item_elem.findtext("link") or "").strip()
        raw_desc = (item_elem.findtext("description") or "").strip()
        pub_date = (item_elem.findtext("pubDate") or "").strip()

        if not title:
            return None

        # Clean HTML from description
        clean_desc = re.sub(r'<[^>]+>', ' ', raw_desc)
        clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()

        # Extract budget from description e.g. "Budget: $250" or "Hourly Range: $30-$50"
        budget_max = 0.0
        budget_min = 0.0
        budget_match = re.search(r'Budget\s*:\s*\$([0-9,]+(?:\.[0-9]+)?)', clean_desc, re.IGNORECASE)
        if budget_match:
            try:
                budget_max = float(budget_match.group(1).replace(',', ''))
                budget_min = budget_max
            except ValueError:
                pass
        else:
            hourly_match = re.search(r'Hourly Range\s*:\s*\$([0-9,]+)-\$([0-9,]+)', clean_desc, re.IGNORECASE)
            if hourly_match:
                try:
                    budget_min = float(hourly_match.group(1).replace(',', ''))
                    budget_max = float(hourly_match.group(2).replace(',', ''))
                except ValueError:
                    pass

        # Check Payment Verified indicator
        payment_verified = "Payment Verified" in raw_desc or "Payment: Verified" in clean_desc

        # Extract unique job key from link
        job_key_match = re.search(r'_~([a-zA-Z0-9]+)', link)
        job_id = job_key_match.group(1) if job_key_match else str(hash(title + link))[-8:]

        return RawJobPosting(
            id=f"up_{job_id}",
            platform=PlatformType.UPWORK,
            title=title,
            description=clean_desc,
            budget_min=budget_min,
            budget_max=budget_max,
            currency="USD",
            client_spend=0.0,
            client_rating=5.0 if payment_verified else 0.0,
            payment_verified=payment_verified,
            skills=["Python", "Automation"],
            published_at=time.time(),
            raw_metadata={"link": link, "raw_pub_date": pub_date}
        )

    def _parse_json_item(self, it: Dict[str, Any]) -> Optional[RawJobPosting]:
        job_id = str(it.get("id") or it.get("ciphertext") or hash(str(it)))[-8:]
        title = it.get("title", "").strip()
        description = it.get("description", "").strip()
        if not title:
            return None

        budget = float(it.get("budget", 0.0) or it.get("amount", 0.0) or 0.0)
        verified = bool(it.get("client_payment_verified", True))

        return RawJobPosting(
            id=f"up_{job_id}",
            platform=PlatformType.UPWORK,
            title=title,
            description=description,
            budget_min=budget,
            budget_max=budget,
            currency=str(it.get("currency", "USD")).upper(),
            client_spend=float(it.get("client_spend", 0.0) or 0.0),
            client_rating=float(it.get("client_rating", 4.9) or 0.0),
            payment_verified=verified,
            skills=it.get("skills", ["Python"]),
            published_at=float(it.get("published_at", time.time())),
            raw_metadata=it
        )
