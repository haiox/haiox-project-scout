"""
Unit and Integration Tests for Phase 4 Genesis Bridge & Proposal Synthesizer
Module: tests/test_bridge.py
"""

import ast
import pytest
from core.schemas import RawJobPosting, PlatformType
from prober.target_prober import TargetInspectionResult, DetectedTech
from bridge.genesis_bridge import GenesisBridge
from bridge.proposal_synthesizer import ProposalSynthesizer


def test_genesis_bridge_ast_validity():
    bridge = GenesisBridge()

    # 1. Shopify Job
    job_shopify = RawJobPosting(
        id="b1", platform=PlatformType.UPWORK, title="Shopify Product Scraper",
        description="Scrape products from our store."
    )
    insp_shopify = TargetInspectionResult(
        url="https://mystore.com",
        is_accessible=True,
        tech_info=DetectedTech(technologies=["Shopify"], has_public_api=True)
    )
    bp1 = bridge.generate_prototype(job_shopify, insp_shopify)
    assert bp1.is_valid_ast is True
    # Verify ast.parse passes directly
    parsed_ast = ast.parse(bp1.code)
    assert parsed_ast is not None
    assert "ECommerceHarvester" in bp1.code

    # 2. API Job
    job_api = RawJobPosting(
        id="b2", platform=PlatformType.FREELANCER, title="REST API Integration",
        description="Connect to remote API and normalize json."
    )
    bp2 = bridge.generate_prototype(job_api, None)
    assert bp2.is_valid_ast is True
    assert "ResilientAPIClient" in bp2.code

    # 3. DOM Scraper Job
    job_dom = RawJobPosting(
        id="b3", platform=PlatformType.REMOTEOK, title="Data Crawler",
        description="Extract tables from target page."
    )
    bp3 = bridge.generate_prototype(job_dom, None)
    assert bp3.is_valid_ast is True
    assert "RobustDataScraper" in bp3.code


def test_proposal_synthesizer_ground_truth_and_3sentences():
    synthesizer = ProposalSynthesizer()

    job = RawJobPosting(
        id="p1",
        platform=PlatformType.FREELANCER,
        title="Extract products with pagination",
        description="Target site https://shop.brand.com needs full extraction.",
        budget_max=250.0,
        currency="USD",
        client_rating=4.9,
        payment_verified=True,
        target_urls=["https://shop.brand.com"]
    )

    inspection = TargetInspectionResult(
        url="https://shop.brand.com",
        is_accessible=True,
        tech_info=DetectedTech(
            technologies=["Shopify"],
            waf_or_protection="Cloudflare WAF / CDN",
            has_public_api=True
        )
    )

    proposal = synthesizer.synthesize(job, inspection, overall_score=92.5)

    # 1. Verify Ground Truth in Sentence 1
    assert "https://shop.brand.com" in proposal.sentence_1_pain_diagnosis
    assert "Shopify" in proposal.sentence_1_pain_diagnosis
    assert "Cloudflare WAF" in proposal.sentence_1_pain_diagnosis

    # 2. Verify Concrete Solution in Sentence 2 (Zero resume talk)
    assert "asynchronous Python pipeline using httpx" in proposal.sentence_2_concrete_solution
    assert "years of experience" not in proposal.sentence_2_concrete_solution.lower()

    # 3. Verify Free Sample Offer in Sentence 3
    assert "working prototype ready" in proposal.sentence_3_free_sample_cta
    assert "sample records" in proposal.sentence_3_free_sample_cta

    # 4. Telegram Card contains metadata and markup
    assert "HAIOX PROJECT SCOUT ALERT" in proposal.telegram_card_markdown
    assert "Score: <b>92.5/100</b>" in proposal.telegram_card_markdown
    assert "$250 USD" in proposal.telegram_card_markdown
