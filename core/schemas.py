"""
Haiox Project Scout - Core Data Schemas & User Filter Preferences
Module: core/schemas.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import hashlib
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class PlatformType(str, Enum):
    FREELANCER = "freelancer"
    UPWORK = "upwork"
    REMOTEOK = "remoteok"
    GURU = "guru"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclass
class RawJobPosting:
    """Standardized representation of a job posting across all inbound platforms."""
    id: str
    platform: PlatformType
    title: str
    description: str
    budget_min: float = 0.0
    budget_max: float = 0.0
    currency: str = "USD"
    client_spend: float = 0.0
    client_rating: float = 0.0
    payment_verified: bool = False
    target_urls: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    published_at: float = field(default_factory=time.time)
    source_url: str = ""
    custom_platform_name: Optional[str] = None
    fingerprint: str = ""
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.fingerprint:
            self.fingerprint = self.compute_fingerprint()
        if not self.target_urls and self.description:
            self.target_urls = self.extract_urls_from_text(self.description)

    def compute_fingerprint(self) -> str:
        """Generates deterministic MD5 hash based on normalized title, budget, and description snippet."""
        clean_title = re.sub(r'\s+', ' ', self.title.strip().lower())
        desc_snippet = re.sub(r'\s+', ' ', self.description[:300].strip().lower())
        sig = f"{self.platform.value}:{clean_title}:{round(self.budget_max, 2)}:{desc_snippet}"
        return hashlib.md5(sig.encode('utf-8')).hexdigest()

    @staticmethod
    def extract_urls_from_text(text: str) -> List[str]:
        """Extracts valid HTTP/HTTPS URLs from raw text."""
        url_pattern = re.compile(
            r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
        )
        found = url_pattern.findall(text)
        seen = set()
        deduped = []
        for u in found:
            clean_u = u.rstrip('.,;:)')
            if clean_u not in seen:
                seen.add(clean_u)
                deduped.append(clean_u)
        return deduped

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "platform": self.platform.value,
            "title": self.title,
            "description": self.description,
            "budget_min": self.budget_min,
            "budget_max": self.budget_max,
            "currency": self.currency,
            "client_spend": self.client_spend,
            "client_rating": self.client_rating,
            "payment_verified": self.payment_verified,
            "target_urls": self.target_urls,
            "skills": self.skills,
            "published_at": self.published_at,
            "source_url": self.source_url,
            "custom_platform_name": self.custom_platform_name,
            "fingerprint": self.fingerprint,
            "raw_metadata": self.raw_metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RawJobPosting":
        data_copy = dict(data)
        if isinstance(data_copy.get("platform"), str):
            data_copy["platform"] = PlatformType(data_copy["platform"])
        return cls(**data_copy)


@dataclass
class UserFilterCriteria:
    """
    User-configurable criteria for filtering opportunities based solely on
    pricing, client quality indicators, and technical alignment.
    No geographic, ethnic, or demographic assumptions.
    """
    min_price: float = 0.0
    max_price: Optional[float] = None
    allowed_currencies: List[str] = field(default_factory=list)  # Empty means all currencies allowed
    required_keywords: List[str] = field(default_factory=list)  # e.g. ["python", "scraping"]
    excluded_keywords: List[str] = field(default_factory=list)  # e.g. ["wordpress", "data entry"]
    min_client_rating: float = 0.0
    payment_verified_only: bool = False
    max_age_minutes: Optional[int] = None  # Freshness threshold e.g. 60 mins

    def matches(self, job: RawJobPosting) -> bool:
        """Evaluates whether a job posting satisfies all selected conditions."""
        # 1. Price Floor Check
        price_to_check = job.budget_max if job.budget_max > 0 else job.budget_min
        if price_to_check > 0 and price_to_check < self.min_price:
            return False

        # 2. Price Ceiling Check
        if self.max_price is not None and price_to_check > self.max_price:
            return False

        # 3. Currency Filter
        if self.allowed_currencies:
            if job.currency.upper() not in [c.upper() for c in self.allowed_currencies]:
                return False

        # 4. Verified Payment Condition
        if self.payment_verified_only and not job.payment_verified:
            return False

        # 5. Client Rating Condition
        if job.client_rating > 0 and job.client_rating < self.min_client_rating:
            return False

        # 6. Age / Freshness Condition
        if self.max_age_minutes is not None:
            age_minutes = (time.time() - job.published_at) / 60.0
            if age_minutes > self.max_age_minutes:
                return False

        # 7. Keyword Inclusion
        text_corpus = f"{job.title} {job.description} {' '.join(job.skills)}".lower()
        if self.required_keywords:
            if not any(k.lower() in text_corpus for k in self.required_keywords):
                return False

        # 8. Keyword Exclusion
        if self.excluded_keywords:
            if any(k.lower() in text_corpus for k in self.excluded_keywords):
                return False

        return True


@dataclass
class CustomSiteSpec:
    """Specification for adding a custom site or feed endpoint by the user."""
    name: str
    feed_url: str
    feed_type: str = "json"  # "json", "rss", or "html"
    rate_limit_delay_seconds: float = 2.0
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class FeedConfig:
    """Configuration parameters for feed polling drivers."""
    timeout_seconds: float = 4.0
    user_agent: str = "HaioxProjectScout/1.0 (+https://haiox.ai)"
    max_items_per_pull: int = 50
    poll_interval_seconds: int = 60
    jitter_range: float = 2.0
