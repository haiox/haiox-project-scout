"""
Unit and Integration Tests for Phase 3 Prober and Tech Stack Analyzer
Module: tests/test_prober.py
"""

import pytest
import httpx
from unittest.mock import patch
from core.schemas import RawJobPosting, PlatformType
from prober.tech_stack_analyzer import TechStackAnalyzer
from prober.target_prober import TargetProber


def test_tech_stack_analyzer_shopify_cloudflare():
    analyzer = TechStackAnalyzer()
    sample_html = """
    <html>
      <head><title>Acme Fashion Store</title></head>
      <body>
        <script src="https://cdn.shopify.com/s/files/theme.js"></script>
        <link rel="stylesheet" href="/products.json">
      </body>
    </html>
    """
    headers = {"server": "cloudflare", "cf-ray": "82a93b482", "content-type": "text/html"}
    result = analyzer.analyze(sample_html, headers, status_code=200, latency_ms=145.0)

    assert "Shopify" in result.technologies
    assert result.waf_or_protection == "Cloudflare WAF / CDN"
    assert result.has_public_api is True
    assert len(result.pain_points) == 0


def test_tech_stack_analyzer_wordpress_and_pain_points():
    analyzer = TechStackAnalyzer()
    sample_html = """
    <html>
      <head><title>Old Blog</title></head>
      <body>
        <link rel="stylesheet" href="/wp-content/themes/sample/style.css">
        <link rel="stylesheet" href="/wp-includes/css/dist/block-library/style.css">
      </body>
    </html>
    """
    headers = {"server": "Apache/2.4.41 (Ubuntu)"}
    # 500 error and 2500ms latency
    result = analyzer.analyze(sample_html, headers, status_code=500, latency_ms=2500.0)

    assert "WordPress" in result.technologies
    assert any("HTTP 500" in p for p in result.pain_points)
    assert any("High response latency" in p for p in result.pain_points)


def test_tech_stack_analyzer_nextjs_react():
    analyzer = TechStackAnalyzer()
    sample_html = """
    <html>
      <head><title>SaaS Dashboard</title></head>
      <body>
        <div id="__next"><script id="__NEXT_DATA__" type="application/json">{}</script></div>
        <script src="/_next/static/chunks/main.js"></script>
      </body>
    </html>
    """
    headers = {"server": "Vercel"}
    result = analyzer.analyze(sample_html, headers, status_code=200, latency_ms=80.0)

    assert "Next.js" in result.frameworks


@pytest.mark.asyncio
async def test_target_prober_mocked_http():
    sample_html = "<html><head><title>Example Online Shop</title></head><body><script src='https://cdn.shopify.com/theme.js'></script></body></html>"
    
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            text=sample_html,
            headers={"server": "cloudflare", "content-type": "text/html"}
        )

    transport = httpx.MockTransport(handler)
    prober = TargetProber(timeout_seconds=5.0)

    # Patch httpx.AsyncClient to use MockTransport
    with patch("httpx.AsyncClient", return_value=httpx.AsyncClient(transport=transport)):
        res = await prober.probe_url("https://example-shop.com")
        assert res.is_accessible is True
        assert res.status_code == 200
        assert res.page_title == "Example Online Shop"
        assert "Shopify" in res.tech_info.technologies
        assert "Example Online Shop" in res.ground_truth_summary


@pytest.mark.asyncio
async def test_target_prober_job_without_urls():
    prober = TargetProber(timeout_seconds=5.0)
    job_no_urls = RawJobPosting(
        id="j_none", platform=PlatformType.FREELANCER, title="Job Without Links",
        description="Just build a script from scratch."
    )
    res_none = await prober.probe_job(job_no_urls)
    assert res_none.is_accessible is False
    assert "No external target URL detected" in res_none.ground_truth_summary


@pytest.mark.asyncio
async def test_target_prober_error_resilience():
    prober = TargetProber(timeout_seconds=1.0)
    # Probing an invalid/non-existent host should fail gracefully without unhandled exception
    res = await prober.probe_url("http://non-existent-domain-xyz-12345.test")
    assert res.is_accessible is False
    assert "Inaccessible / Connection error" in res.ground_truth_summary
