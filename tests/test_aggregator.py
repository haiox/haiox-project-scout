"""
Tests for Feed Aggregator, Dynamic User Sites & Preference Filtering
Module: tests/test_aggregator.py
"""

import time
import pytest
from typing import List
from core.schemas import RawJobPosting, PlatformType, UserFilterCriteria, CustomSiteSpec
from ingestion.base import BaseFeedDriver
from ingestion.aggregator import FeedAggregator


class MockDriver(BaseFeedDriver):
    def __init__(self, platform: PlatformType, jobs: List[RawJobPosting]):
        super().__init__(platform)
        self.mock_jobs = jobs

    async def fetch_jobs(self) -> List[RawJobPosting]:
        return self.mock_jobs

    def parse_payload(self, raw_data):
        return self.mock_jobs


@pytest.mark.asyncio
async def test_aggregator_with_user_filters_and_custom_site():
    now = time.time()
    # 4 jobs from different platforms with different prices
    job1 = RawJobPosting(id="fl_1", platform=PlatformType.FREELANCER, title="Python Scraper", description="Extract data", budget_max=180.0, currency="USD", payment_verified=True, published_at=now - 50)
    job2 = RawJobPosting(id="up_2", platform=PlatformType.UPWORK, title="Data Entry (Exclude)", description="Manual entry", budget_max=25.0, currency="USD", payment_verified=True, published_at=now)
    job3 = RawJobPosting(id="cst_3", platform=PlatformType.CUSTOM, custom_platform_name="NicheHub", title="FastAPI Microservice", description="Python backend", budget_max=350.0, currency="USD", payment_verified=True, published_at=now - 10)

    d1 = MockDriver(PlatformType.FREELANCER, [job1])
    d2 = MockDriver(PlatformType.UPWORK, [job2])
    d3 = MockDriver(PlatformType.CUSTOM, [job3])

    aggregator = FeedAggregator(drivers=[d1, d2, d3])

    # User Condition: Minimum price $100, must contain 'python'
    criteria = UserFilterCriteria(
        min_price=100.0,
        required_keywords=["python"],
        payment_verified_only=True
    )

    filtered_jobs, metrics = await aggregator.poll_all(filter_criteria=criteria)

    # Job2 ($25) is filtered out because it is below $100 price floor!
    assert len(filtered_jobs) == 2
    assert metrics["total_fetched"] == 3
    assert metrics["passed_user_filter"] == 2
    assert metrics["filtered_by_user_criteria"] == 1

    # Order by freshness: job3 (now - 10) -> job1 (now - 50)
    assert filtered_jobs[0].id == "cst_3"
    assert filtered_jobs[1].id == "fl_1"


@pytest.mark.asyncio
async def test_aggregator_dynamic_custom_site_registration():
    aggregator = FeedAggregator(drivers=[])
    spec = CustomSiteSpec(name="UserCustomBoard", feed_url="https://example.com/api")
    driver = aggregator.add_custom_site(spec)

    assert len(aggregator.drivers) == 1
    assert aggregator.drivers[0].platform == PlatformType.CUSTOM
