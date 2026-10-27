"""
Haiox Project Scout - Freelancer.com Ingestion Driver
Module: ingestion/freelancer_driver.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import time
import logging
from typing import List, Dict, Any, Optional

from core.schemas import RawJobPosting, PlatformType, FeedConfig
from .base import BaseFeedDriver

logger = logging.getLogger("project_scout.freelancer")


class FreelancerFeedDriver(BaseFeedDriver):
    """Driver for extracting active opportunities from Freelancer.com public API / feeds."""

    API_URL = "https://www.freelancer.com/api/projects/0.1/projects/active/"

    def __init__(self, config: Optional[FeedConfig] = None):
        super().__init__(PlatformType.FREELANCER, config)

    async def fetch_jobs(self) -> List[RawJobPosting]:
        params = {
            "compact": "true",
            "limit": str(self.config.max_items_per_pull),
            "project_types[]": "fixed",
            "languages[]": "en",
            "sort_field": "time_updated",
            "reverse_sort": "true"
        }
        resp = await self._safe_http_get(self.API_URL, params=params)
        if not resp:
            return []

        try:
            data = resp.json()
            return self.parse_payload(data)
        except Exception as exc:
            logger.error(f"[Freelancer] Failed to parse JSON response: {exc}")
            return []

    def parse_payload(self, raw_data: Any) -> List[RawJobPosting]:
        items: List[RawJobPosting] = []
        if not isinstance(raw_data, dict):
            return items

        projects = raw_data.get("result", {}).get("projects", [])
        if not isinstance(projects, list):
            # Also support direct list if mock payload provided
            projects = raw_data.get("projects", [])

        for p in projects:
            try:
                p_id = str(p.get("id", ""))
                if not p_id:
                    continue

                title = p.get("title", "").strip()
                description = p.get("preview_description", "") or p.get("description", "")
                
                budget_info = p.get("budget", {}) or {}
                budget_min = float(budget_info.get("minimum", 0.0) or 0.0)
                budget_max = float(budget_info.get("maximum", 0.0) or budget_min)

                curr_info = p.get("currency", {}) or {}
                currency = str(curr_info.get("code", "USD")).upper()

                owner = p.get("owner", {}) or {}
                rep = owner.get("reputation", {}).get("entire_history", {}) or {}
                client_rating = float(rep.get("rating", 0.0) or 0.0)
                client_spend = float(owner.get("total_spent", 0.0) or 0.0)
                status = owner.get("status", {}) or {}
                payment_verified = bool(status.get("payment_verified", False))

                raw_skills = p.get("jobs", []) or []
                skills = [s.get("name", "") for s in raw_skills if isinstance(s, dict) and s.get("name")]

                submit_date = p.get("submitdate", 0)
                published_at = float(submit_date) if submit_date else time.time()

                job = RawJobPosting(
                    id=f"fl_{p_id}",
                    platform=PlatformType.FREELANCER,
                    title=title,
                    description=description,
                    budget_min=budget_min,
                    budget_max=budget_max,
                    currency=currency,
                    client_spend=client_spend,
                    client_rating=client_rating,
                    payment_verified=payment_verified,
                    skills=skills,
                    published_at=published_at,
                    raw_metadata={"raw_id": p_id, "url": f"https://www.freelancer.com/projects/{p_id}"}
                )
                items.append(job)
            except Exception as item_err:
                logger.debug(f"[Freelancer] Skipping malformed item: {item_err}")
                continue

        return items
