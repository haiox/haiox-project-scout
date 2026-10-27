"""
Haiox Project Scout - Tech Stack & Pain Points Analyzer
Module: prober/tech_stack_analyzer.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DetectedTech:
    """Represents technology fingerprints detected on the target site."""
    technologies: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    waf_or_protection: Optional[str] = None
    has_public_api: bool = False
    pain_points: List[str] = field(default_factory=list)


class TechStackAnalyzer:
    """Analyzes response headers, status codes, and HTML content to extract technical ground truth."""

    # Technology Signature Rules
    TECH_SIGNATURES: Dict[str, List[str]] = {
        "Shopify": [r"cdn\.shopify\.com", r"Shopify\.theme", r"/products\.json"],
        "WordPress": [r"wp-content", r"wp-includes", r"xmlrpc\.php"],
        "WooCommerce": [r"woocommerce", r"wc-api"],
        "Magento": [r"mage/cookies", r"skin/frontend", r"/static/version"],
        "Next.js": [r"__NEXT_DATA__", r"/_next/static"],
        "Nuxt.js": [r"__NUXT__", r"/_nuxt/"],
        "React": [r"react", r"data-reactroot"],
        "Vue.js": [r"vue", r"v-cloak"],
        "FastAPI / OpenAPI": [r"swagger-ui", r"/docs", r"/openapi\.json"],
        "GraphQL": [r"/graphql", r"__typename"],
    }

    def analyze(self, html: str, headers: Dict[str, str], status_code: int, latency_ms: float) -> DetectedTech:
        detected_techs: List[str] = []
        frameworks: List[str] = []
        pain_points: List[str] = []
        waf_detected: Optional[str] = None
        has_api: bool = False

        headers_lower = {k.lower(): v.lower() for k, v in headers.items()}
        server_header = headers_lower.get("server", "")

        # 1. Server & WAF Detection
        if "cloudflare" in server_header or "cf-ray" in headers_lower:
            waf_detected = "Cloudflare WAF / CDN"
        elif "akamai" in server_header:
            waf_detected = "Akamai Edge"
        elif "fastly" in server_header:
            waf_detected = "Fastly CDN"

        # 2. Status Code & Latency Pain Points
        if status_code >= 500:
            pain_points.append(f"Server returning HTTP {status_code} internal error")
        elif status_code == 403:
            pain_points.append("Strict access control or WAF block (HTTP 403 Forbidden)")
        elif status_code == 404:
            pain_points.append("Target endpoint returning HTTP 404 Not Found")

        if latency_ms > 2000:
            pain_points.append(f"High response latency detected ({round(latency_ms / 1000, 2)}s)")

        # 3. HTML Content Inspection
        html_lower = html.lower()

        for tech, patterns in self.TECH_SIGNATURES.items():
            for pat in patterns:
                if re.search(pat, html_lower):
                    if tech in ["Shopify", "WordPress", "WooCommerce", "Magento"]:
                        if tech not in detected_techs:
                            detected_techs.append(tech)
                    elif tech in ["Next.js", "Nuxt.js", "React", "Vue.js"]:
                        if tech not in frameworks:
                            frameworks.append(tech)
                    elif tech in ["FastAPI / OpenAPI", "GraphQL"]:
                        has_api = True
                        if tech not in detected_techs:
                            detected_techs.append(tech)
                    break

        # Check for Public API clues
        if "json" in headers_lower.get("content-type", "") or "/api/" in html_lower or "/products.json" in html_lower:
            has_api = True

        return DetectedTech(
            technologies=detected_techs,
            frameworks=frameworks,
            waf_or_protection=waf_detected,
            has_public_api=has_api,
            pain_points=pain_points
        )
