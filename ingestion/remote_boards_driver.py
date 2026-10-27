"""
Haiox Bounty Hunter - Remote Boards Ingestion Driver
Module: ingestion/remote_boards_driver.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import re
import time
import logging
from typing import List, Dict, Any, Optional

from core.schemas import RawJobPosting, PlatformType, FeedConfig
from .base import BaseFeedDriver

logger = logging.getLogger("bounty_hunter.remote_boards")


class RemoteBoardsDriver(BaseFeedDriver):
    """Driver for extracting high-yield remote Python/AI contract opportunities (RemoteOK & CryptoJobs)."""

    REMOTEOK_API = "https://remoteok.com/api"

    def __init__(self, config: Optional[FeedConfig] = None):
        super().__init__(PlatformType.REMOTEOK, config)

    async def fetch_jobs(self) -> List[RawJobPosting]:
        resp = await self._safe_http_get(self.REMOTEOK_API)
        if not resp:
            return []

        try:
            data = resp.json()
            return self.parse_payload(data)
        except Exception as e:
            logger.error(f"[RemoteBoards] Failed to parse JSON: {e}")
            return []

    def parse_payload(self, raw_data: Any) -> List[RawJobPosting]:
        items: List[RawJobPosting] = []
        if not isinstance(raw_data, list):
            return items

        for entry in raw_data:
            if not isinstance(entry, dict):
                continue

            # First element of RemoteOK API is legal disclaimer dictionary
            if "legal" in entry or not entry.get("id"):
                continue

            try:
                job_id = str(entry.get("id"))
                position = str(entry.get("position", "")).strip()
                company = str(entry.get("company", "")).strip()
                title = f"{position} at {company}" if company else position
                raw_desc = str(entry.get("description", ""))
                clean_desc = re.sub(r'<[^>]+>', ' ', raw_desc)
                clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()

                # Extract budget / salary
                salary_min = float(entry.get("salary_min", 0.0) or 0.0)
                salary_max = float(entry.get("salary_max", 0.0) or salary_min)
                
                # If salary is annual (e.g. 80,000), approximate contract / project equivalent
                # For micro-tasks / hourly, standard numbers are < 5000
                tags = entry.get("tags", []) or []
                url = entry.get("url", f"https://remoteok.com/l/{job_id}")
                epoch = float(entry.get("epoch", 0) or 0)
                published_at = epoch if epoch > 0 else time.time()

                job = RawJobPosting(
                    id=f"rok_{job_id}",
                    platform=PlatformType.REMOTEOK,
                    title=title,
                    description=clean_desc,
                    budget_min=salary_min,
                    budget_max=salary_max,
                    currency="USD",
                    client_spend=10000.0,  # RemoteOK listings are paid $299+ by verified companies
                    client_rating=5.0,
                    payment_verified=True,
                    skills=tags,
                    published_at=published_at,
                    raw_metadata={"url": url, "company": company, "apply_url": entry.get("apply_url", "")}
                )
                items.append(job)
            except Exception as err:
                logger.debug(f"[RemoteBoards] Skipping item: {err}")
                continue

        return items
