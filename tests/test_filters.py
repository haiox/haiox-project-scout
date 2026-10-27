"""
Unit and Integration Tests for Phase 2 Filters and Quality Gate
Module: tests/test_filters.py
"""

import pytest
import time
from core.schemas import RawJobPosting, PlatformType, UserFilterCriteria
from filters.price_guard import CurrencyConverter, PriceGuard
from filters.keyword_matcher import KeywordMatcher
from filters.client_reputation import ClientReputationGuard
from filters.quality_gate import QualityGate


def test_currency_converter():
    converter = CurrencyConverter()
    assert converter.to_usd(100.0, "USD") == 100.0
    assert converter.to_usd(100.0, "EUR") == 108.0
    assert converter.to_usd(100.0, "GBP") == 130.0
    assert converter.to_usd(1000.0, "AUD") == 650.0
    # Fallback to 1.0 for unknown currency
    assert converter.to_usd(50.0, "XYZ") == 50.0


def test_price_guard_thresholds():
    guard = PriceGuard()
    criteria = UserFilterCriteria(min_price=100.0, max_price=500.0)

    # Job below floor
    job_low = RawJobPosting(
        id="j1", platform=PlatformType.FREELANCER, title="Tiny Job", description="small",
        budget_max=50.0, currency="USD"
    )
    passed, usd, reason = guard.evaluate(job_low, criteria)
    assert not passed
    assert usd == 50.0
    assert "below floor" in reason

    # Job above ceiling
    job_high = RawJobPosting(
        id="j2", platform=PlatformType.FREELANCER, title="Huge Job", description="big",
        budget_max=1000.0, currency="USD"
    )
    passed, usd, reason = guard.evaluate(job_high, criteria)
    assert not passed
    assert usd == 1000.0
    assert "exceeds ceiling" in reason

    # Job within range in EUR (150 EUR * 1.08 = 162 USD)
    job_ok = RawJobPosting(
        id="j3", platform=PlatformType.UPWORK, title="Medium Job", description="normal",
        budget_max=150.0, currency="EUR"
    )
    passed, usd, reason = guard.evaluate(job_ok, criteria)
    assert passed
    assert usd == 162.0
    assert reason is None


def test_price_guard_allowed_currencies():
    guard = PriceGuard()
    criteria = UserFilterCriteria(allowed_currencies=["USD", "EUR"])

    job_valid = RawJobPosting(id="j1", platform=PlatformType.FREELANCER, title="Job", description="", currency="USD")
    job_invalid = RawJobPosting(id="j2", platform=PlatformType.FREELANCER, title="Job", description="", currency="JPY")

    assert guard.evaluate(job_valid, criteria)[0] is True
    assert guard.evaluate(job_invalid, criteria)[0] is False


def test_keyword_matcher_required_and_excluded():
    matcher = KeywordMatcher()

    criteria = UserFilterCriteria(
        required_keywords=["python", "scraper"],
        excluded_keywords=["wordpress", "php"]
    )

    # Match required, no excluded
    job_good = RawJobPosting(
        id="j1", platform=PlatformType.REMOTEOK, title="Python Scraper Engineer",
        description="Build an async crawler using Playwright or httpx.",
        skills=["Python"]
    )
    passed, score, reason = matcher.evaluate(job_good, criteria)
    assert passed
    assert score > 0.0

    # Contains excluded keyword
    job_bad = RawJobPosting(
        id="j2", platform=PlatformType.FREELANCER, title="Python WordPress Bridge",
        description="Need a Python script to post to my WordPress site.",
        skills=["Python", "WordPress"]
    )
    passed, score, reason = matcher.evaluate(job_bad, criteria)
    assert not passed
    assert "Excluded keyword detected: 'wordpress'" in reason

    # Missing required keywords
    job_irrelevant = RawJobPosting(
        id="j3", platform=PlatformType.GURU, title="Java Backend",
        description="Spring Boot microservice development.",
        skills=["Java"]
    )
    passed, score, reason = matcher.evaluate(job_irrelevant, criteria)
    assert not passed
    assert "None of the required keywords matched" in reason


def test_client_reputation_guard():
    guard = ClientReputationGuard()
    criteria = UserFilterCriteria(
        min_client_rating=4.5,
        payment_verified_only=True,
        max_age_minutes=60
    )

    # Compliant client
    job_ok = RawJobPosting(
        id="j1", platform=PlatformType.UPWORK, title="Scrape e-commerce", description="help",
        client_rating=4.8, payment_verified=True, published_at=time.time() - 300  # 5 min ago
    )
    passed, trust, reason = guard.evaluate(job_ok, criteria)
    assert passed
    assert trust >= 0.75

    # Unverified payment
    job_unverified = RawJobPosting(
        id="j2", platform=PlatformType.UPWORK, title="Scrape e-commerce", description="help",
        client_rating=4.8, payment_verified=False, published_at=time.time() - 300
    )
    passed, _, reason = guard.evaluate(job_unverified, criteria)
    assert not passed
    assert "payment method is unverified" in reason

    # Low rating
    job_low_rating = RawJobPosting(
        id="j3", platform=PlatformType.UPWORK, title="Scrape e-commerce", description="help",
        client_rating=3.9, payment_verified=True, published_at=time.time() - 300
    )
    passed, _, reason = guard.evaluate(job_low_rating, criteria)
    assert not passed
    assert "below threshold" in reason


def test_quality_gate_unified():
    gate = QualityGate()
    criteria = UserFilterCriteria(
        min_price=50.0,
        max_price=1000.0,
        required_keywords=["python"],
        excluded_keywords=["data entry"],
        payment_verified_only=True
    )

    # Perfect Opportunity with Target URL
    job = RawJobPosting(
        id="q1",
        platform=PlatformType.FREELANCER,
        title="High Performance Python Scraper",
        description="We need an async Python scraper for https://targetstore.com/products/api to harvest stock.",
        budget_max=300.0,
        currency="USD",
        payment_verified=True,
        client_rating=4.9,
        published_at=time.time() - 120
    )

    decision = gate.evaluate(job, criteria)
    assert decision.passed is True
    assert decision.overall_score >= 80.0
    assert decision.has_target_urls is True
    assert decision.target_urls_count == 1
    assert "Price verified ($300.0 USD equivalent)" in decision.reasons[0]
    assert decision.breakdown["target_bonus"] == 15.0
