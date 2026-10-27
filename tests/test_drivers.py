"""
Tests for Ingestion Platform Drivers & Custom User Sites
Module: tests/test_drivers.py
"""

import pytest
from core.schemas import PlatformType, CustomSiteSpec
from ingestion.freelancer_driver import FreelancerFeedDriver
from ingestion.upwork_driver import UpworkFeedDriver
from ingestion.remote_boards_driver import RemoteBoardsDriver
from ingestion.local_driver import LocalFeedDriver
from ingestion.custom_driver import CustomSiteDriver


def test_freelancer_driver_parsing():
    driver = FreelancerFeedDriver()
    mock_payload = {
        "result": {
            "projects": [
                {
                    "id": 1234567,
                    "title": "Python Product Scraper",
                    "preview_description": "Scrape product prices from https://sample-store.com/deals daily.",
                    "budget": {"minimum": 150.0, "maximum": 300.0},
                    "currency": {"code": "USD"},
                    "owner": {
                        "reputation": {"entire_history": {"rating": 4.9}},
                        "total_spent": 4500.0,
                        "status": {"payment_verified": True}
                    },
                    "jobs": [{"name": "Python"}, {"name": "Web Scraping"}],
                    "submitdate": 1729000000
                }
            ]
        }
    }

    jobs = driver.parse_payload(mock_payload)
    assert len(jobs) == 1
    j = jobs[0]
    assert j.id == "fl_1234567"
    assert j.platform == PlatformType.FREELANCER
    assert j.budget_max == 300.0
    assert j.payment_verified is True


def test_upwork_rss_xml_parsing():
    driver = UpworkFeedDriver()
    mock_rss = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Upwork Jobs</title>
            <item>
                <title>Automated Selenium Bot with Proxy Rotation</title>
                <link>https://www.upwork.com/jobs/_~01a2b3c4d5e6f7</link>
                <description><![CDATA[
                    Need a robust scraper for https://realestate.com.
                    <b>Budget:</b> $350.
                    <b>Payment:</b> Verified.
                ]]></description>
                <pubDate>Tue, 27 Oct 2026 03:00:00 +0000</pubDate>
            </item>
        </channel>
    </rss>
    """

    jobs = driver.parse_payload(mock_rss)
    assert len(jobs) == 1
    j = jobs[0]
    assert j.platform == PlatformType.UPWORK
    assert j.budget_max == 350.0
    assert j.payment_verified is True


def test_remote_boards_driver_parsing():
    driver = RemoteBoardsDriver()
    mock_payload = [
        {"legal": "disclaimer text must be skipped"},
        {
            "id": "job_9981",
            "position": "Senior Python Automation Engineer",
            "company": "Nexus Technologies",
            "description": "<p>Build high-frequency webhooks with FastAPI and Docker. Apply at https://nexus.io/apply</p>",
            "salary_min": 5000,
            "salary_max": 8000,
            "tags": ["python", "api", "docker"],
            "url": "https://remoteok.com/l/job_9981",
            "epoch": 1729050000
        }
    ]

    jobs = driver.parse_payload(mock_payload)
    assert len(jobs) == 1
    assert jobs[0].platform == PlatformType.REMOTEOK
    assert "Nexus Technologies" in jobs[0].title


def test_driver_malformed_payload_graceful_handling():
    fl = FreelancerFeedDriver().parse_payload({"corrupted": "bad_tree"})
    up = UpworkFeedDriver().parse_payload("not_xml_or_json")
    ro = RemoteBoardsDriver().parse_payload("string_instead_of_list")
    loc = LocalFeedDriver().parse_payload(None)

    assert fl == []
    assert up == []
    assert ro == []
    assert loc == []


def test_custom_user_site_driver_parsing():
    spec = CustomSiteSpec(
        name="CryptoGigBoard",
        feed_url="https://cryptogigs.example/api/feed",
        feed_type="json"
    )
    driver = CustomSiteDriver(spec)

    mock_custom_payload = {
        "items": [
            {
                "id": "cg_101",
                "title": "Solana Node Telemetry Bot",
                "description": "Build an alert bot for RPC latency at https://rpc.solana.com",
                "price": 450.0,
                "currency": "USDC",
                "payment_verified": True
            }
        ]
    }

    jobs = driver.parse_payload(mock_custom_payload)
    assert len(jobs) == 1
    j = jobs[0]
    assert j.platform == PlatformType.CUSTOM
    assert j.custom_platform_name == "CryptoGigBoard"
    assert j.budget_max == 450.0
    assert j.currency == "USDC"
    assert "https://rpc.solana.com" in j.target_urls


def test_local_driver_parsing():
    driver = LocalFeedDriver()
    mock_payload = {
        "projects": [
            {
                "id": "loc_7712",
                "title": "Python Data Extraction Script",
                "description": "Extract data from https://target-store.com",
                "budget_min": 2000000,
                "budget_max": 5000000,
                "currency": "TOMAN",
                "is_verified": True
            }
        ]
    }

    jobs = driver.parse_payload(mock_payload)
    assert len(jobs) == 1
    assert jobs[0].platform == PlatformType.LOCAL
    assert jobs[0].currency == "TOMAN"
