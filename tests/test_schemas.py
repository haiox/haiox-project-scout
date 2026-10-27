"""
Tests for Core Schemas, Data Structures & User Filter Preferences
Module: tests/test_schemas.py
"""

import pytest
from core.schemas import RawJobPosting, PlatformType, UserFilterCriteria, CustomSiteSpec


def test_raw_job_posting_initialization():
    job = RawJobPosting(
        id="test_01",
        platform=PlatformType.FREELANCER,
        title="Python Data Scraper",
        description="Extract deals from https://shop.com/deals daily.",
        budget_min=150.0,
        budget_max=300.0,
        currency="USD"
    )

    assert job.id == "test_01"
    assert job.platform == PlatformType.FREELANCER
    assert job.budget_max == 300.0
    assert len(job.fingerprint) == 32  # Valid MD5 hash
    assert job.target_urls == ["https://shop.com/deals"]


def test_user_filter_criteria_price_and_conditions():
    # User wants: min $80, max $500, USD only, verified payment only, python keyword
    criteria = UserFilterCriteria(
        min_price=80.0,
        max_price=500.0,
        allowed_currencies=["USD"],
        required_keywords=["python"],
        payment_verified_only=True
    )

    qualifying_job = RawJobPosting(
        id="q1",
        platform=PlatformType.FREELANCER,
        title="Python Automation Script",
        description="Write a clean Python script for data processing.",
        budget_max=250.0,
        currency="USD",
        payment_verified=True
    )

    too_cheap_job = RawJobPosting(
        id="q2",
        platform=PlatformType.UPWORK,
        title="Python Mini Fix",
        description="Quick python bug",
        budget_max=30.0,
        currency="USD",
        payment_verified=True
    )

    wrong_currency_job = RawJobPosting(
        id="q3",
        platform=PlatformType.LOCAL,
        title="Python Scraper",
        description="Scrape site",
        budget_max=200.0,
        currency="EUR",
        payment_verified=True
    )

    unverified_client_job = RawJobPosting(
        id="q4",
        platform=PlatformType.FREELANCER,
        title="Python Developer",
        description="Scrape e-commerce",
        budget_max=300.0,
        currency="USD",
        payment_verified=False
    )

    assert criteria.matches(qualifying_job) is True
    assert criteria.matches(too_cheap_job) is False
    assert criteria.matches(wrong_currency_job) is False
    assert criteria.matches(unverified_client_job) is False


def test_fingerprint_determinism():
    job1 = RawJobPosting(
        id="job_a",
        platform=PlatformType.UPWORK,
        title="FastAPI Webhook Listener",
        description="Build secure listener with HMAC auth",
        budget_max=200.0
    )

    job2 = RawJobPosting(
        id="job_b",
        platform=PlatformType.UPWORK,
        title="FastAPI Webhook Listener",
        description="Build secure listener with HMAC auth",
        budget_max=200.0
    )

    assert job1.fingerprint == job2.fingerprint


def test_url_extraction():
    text = "Check out https://api.myclient.com/docs and http://shop.co.uk:9000/feed"
    urls = RawJobPosting.extract_urls_from_text(text)
    assert len(urls) == 2
    assert "https://api.myclient.com/docs" in urls
