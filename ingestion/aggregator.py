"""
Haiox Project Scout - Multi-Platform Aggregator & User Preference Filter Hub
Module: ingestion/aggregator.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import asyncio
import logging
import time
from typing import List, Dict, Set, Optional, Tuple, Any

from core.schemas import RawJobPosting, PlatformType, FeedConfig, UserFilterCriteria, CustomSiteSpec
from .base import BaseFeedDriver
from .freelancer_driver import FreelancerFeedDriver
from .upwork_driver import UpworkFeedDriver
from .remote_boards_driver import RemoteBoardsDriver
from .local_driver import LocalFeedDriver
from .custom_driver import CustomSiteDriver

logger = logging.getLogger("project_scout.aggregator")


class FeedAggregator:
    """
    Central Multi-Platform Aggregation & Ingestion Hub for Haiox Project Scout.
    Features:
    1. Polling across major platforms (Freelancer, Upwork, RemoteOK, Local).
    2. Dynamic User-Extensible site registration via CustomSiteSpec.
    3. Cryptographic deduplication (MD5 fingerprints).
    4. User-controlled pricing and quality filtering (Zero geographic bias).
    """

    def __init__(
        self,
        drivers: Optional[List[BaseFeedDriver]] = None,
        config: Optional[FeedConfig] = None,
        max_cache_size: int = 5000
    ):
        self.config = config or FeedConfig()
        self.drivers: List[BaseFeedDriver] = drivers if drivers is not None else [
            FreelancerFeedDriver(self.config),
            UpworkFeedDriver(self.config),
            RemoteBoardsDriver(self.config),
            LocalFeedDriver(self.config)
        ]
        self.seen_fingerprints: Set[str] = set()
        self.max_cache_size = max_cache_size
        self.last_poll_time: float = 0.0

    def register_driver(self, driver: BaseFeedDriver):
        """Adds an existing driver instance to the polling roster."""
        self.drivers.append(driver)

    def add_custom_site(self, spec: CustomSiteSpec) -> CustomSiteDriver:
        """Enables the user to add any custom site, API, or RSS feed dynamically."""
        driver = CustomSiteDriver(spec, self.config)
        self.register_driver(driver)
        logger.info(f"Registered custom user-defined site: {spec.name} ({spec.feed_url})")
        return driver

    async def poll_all(
        self,
        filter_criteria: Optional[UserFilterCriteria] = None
    ) -> Tuple[List[RawJobPosting], Dict[str, Any]]:
        """
        Polls all registered platform drivers concurrently.
        Performs deduplication, optional user preference filtering, and time sorting.
        """
        start_time = time.perf_counter()
        tasks = [driver.fetch_jobs() for driver in self.drivers]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)

        raw_jobs: List[RawJobPosting] = []
        platform_counts: Dict[str, int] = {}
        errors: List[str] = []

        for idx, res in enumerate(results):
            driver = self.drivers[idx]
            driver_name = driver.spec.name if hasattr(driver, "spec") else driver.platform.value
            if isinstance(res, Exception):
                logger.error(f"[Aggregator] Error from {driver_name}: {res}")
                errors.append(f"{driver_name}: {str(res)}")
            elif isinstance(res, list):
                raw_jobs.extend(res)
                platform_counts[driver_name] = len(res)

        # Deduplication
        new_jobs: List[RawJobPosting] = []
        duplicates_count = 0

        for job in raw_jobs:
            if not job.fingerprint:
                job.fingerprint = job.compute_fingerprint()

            if job.fingerprint in self.seen_fingerprints:
                duplicates_count += 1
                continue

            self.seen_fingerprints.add(job.fingerprint)
            new_jobs.append(job)

        # Cache bound enforcement
        if len(self.seen_fingerprints) > self.max_cache_size:
            excess = len(self.seen_fingerprints) - self.max_cache_size
            self.seen_fingerprints = set(list(self.seen_fingerprints)[excess:])

        # Apply User Selected Filter Conditions (if provided)
        filtered_out_count = 0
        final_jobs: List[RawJobPosting] = []

        if filter_criteria is not None:
            for job in new_jobs:
                if filter_criteria.matches(job):
                    final_jobs.append(job)
                else:
                    filtered_out_count += 1
        else:
            final_jobs = new_jobs

        # Sort by freshness (newest first)
        final_jobs.sort(key=lambda j: j.published_at, reverse=True)
        duration = round(time.perf_counter() - start_time, 3)
        self.last_poll_time = time.time()

        metrics = {
            "total_fetched": len(raw_jobs),
            "new_unique_jobs": len(new_jobs),
            "passed_user_filter": len(final_jobs),
            "filtered_by_user_criteria": filtered_out_count,
            "duplicates_filtered": duplicates_count,
            "duration_seconds": duration,
            "platform_breakdown": platform_counts,
            "errors": errors
        }

        return final_jobs, metrics

    def clear_cache(self):
        """Clears the deduplication cache."""
        self.seen_fingerprints.clear()
