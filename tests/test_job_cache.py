"""
Unit and Latency Benchmark Tests for In-Memory Opportunity Cache
Module: tests/test_job_cache.py
"""

import time
from typing import Tuple
import pytest
from core.schemas import RawJobPosting, PlatformType
from core.job_cache import OpportunityCache, CachedOpportunity
from filters.quality_gate import FilterDecision
from bridge.proposal_synthesizer import SynthesizedProposal, SolutionBlueprint


def make_dummy_opp(id: str, title: str, budget: float, platform: PlatformType, score: float) -> Tuple[RawJobPosting, FilterDecision, SynthesizedProposal]:
    job = RawJobPosting(
        id=id,
        platform=platform,
        title=title,
        description=f"Details for {title}",
        budget_max=budget,
        currency="USD"
    )
    dec = FilterDecision(job_id=id, passed=True, overall_score=score, normalized_usd_price=budget)
    prop = SynthesizedProposal(
        job_id=id,
        sentence_1_pain_diagnosis="Diagnosis",
        sentence_2_concrete_solution="Solution",
        sentence_3_free_sample_cta="Sample",
        full_proposal_text="Full text",
        blueprint=SolutionBlueprint(code="print('ok')"),
        telegram_card_markdown="Card"
    )
    return job, dec, prop


def test_cache_sub_millisecond_search():
    cache = OpportunityCache(max_capacity=100)

    # 1. Seed Cache with diverse opportunities
    j1, d1, p1 = make_dummy_opp("p1", "Python Web Scraper", 250.0, PlatformType.FREELANCER, 95.0)
    j2, d2, p2 = make_dummy_opp("r1", "React Next.js Frontend", 500.0, PlatformType.UPWORK, 88.0)
    j3, d3, p3 = make_dummy_opp("p2", "Small Python Task", 40.0, PlatformType.REMOTEOK, 75.0)

    cache.add(j1, d1, p1)
    cache.add(j2, d2, p2)
    cache.add(j3, d3, p3)

    assert cache.count() == 3

    # Benchmark query latency
    t0 = time.perf_counter()
    matches_python = cache.search(keywords=["python"], min_budget=100.0)
    latency_ms = (time.perf_counter() - t0) * 1000

    # Must be sub-millisecond (< 5.0ms)
    assert latency_ms < 5.0
    assert len(matches_python) == 1
    assert matches_python[0].job.id == "p1"

    # Query React
    matches_react = cache.search(keywords=["react"], min_budget=300.0)
    assert len(matches_react) == 1
    assert matches_react[0].job.id == "r1"


def test_cache_deduplication_and_eviction():
    cache = OpportunityCache(max_capacity=2)

    j1, d1, p1 = make_dummy_opp("1", "Job One", 100.0, PlatformType.FREELANCER, 90.0)
    j2, d2, p2 = make_dummy_opp("2", "Job Two", 200.0, PlatformType.UPWORK, 85.0)
    j3, d3, p3 = make_dummy_opp("3", "Job Three", 300.0, PlatformType.REMOTEOK, 80.0)

    # Add 1 and 2
    cache.add(j1, d1, p1)
    cache.add(j1, d1, p1)  # Duplicate add
    assert cache.count() == 1

    cache.add(j2, d2, p2)
    assert cache.count() == 2

    # Adding 3 should evict oldest (1)
    time.sleep(0.01)
    cache.add(j3, d3, p3)
    assert cache.count() == 2
    assert "1" not in cache._cache
    assert "2" in cache._cache
    assert "3" in cache._cache
