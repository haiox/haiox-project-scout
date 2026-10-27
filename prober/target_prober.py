"""
Haiox Project Scout - Target URL Prober & Ground Truth Harvester
Module: prober/target_prober.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import re
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import httpx

from core.schemas import RawJobPosting
from .tech_stack_analyzer import TechStackAnalyzer, DetectedTech


@dataclass
class TargetInspectionResult:
    """Ground truth inspection findings for a specific client target URL."""
    url: str
    is_accessible: bool
    status_code: int = 0
    latency_ms: float = 0.0
    page_title: str = ""
    tech_info: DetectedTech = field(default_factory=DetectedTech)
    ground_truth_summary: str = ""


class TargetProber:
    """
    Asynchronous network probe to inspect client target URLs and extract
    actionable technical ground truth before proposal synthesis.
    """

    def __init__(
        self,
        timeout_seconds: float = 8.0,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        analyzer: Optional[TechStackAnalyzer] = None
    ):
        self.timeout = timeout_seconds
        self.user_agent = user_agent
        self.analyzer = analyzer or TechStackAnalyzer()

    @staticmethod
    def _extract_title(html: str) -> str:
        """Extracts text content of HTML <title> tag."""
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if match:
            clean = re.sub(r"\s+", " ", match.group(1)).strip()
            return clean[:120]
        return ""

    async def probe_url(self, url: str) -> TargetInspectionResult:
        """Probes a single URL with polite HTTP GET and analyzes response."""
        headers = {"User-Agent": self.user_agent, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, verify=False) as client:
                resp = await client.get(url, headers=headers)
                latency_ms = round((time.time() - start_time) * 1000, 2)
                html = resp.text
                status = resp.status_code
                title = self._extract_title(html)

                tech_info = self.analyzer.analyze(
                    html=html,
                    headers=dict(resp.headers),
                    status_code=status,
                    latency_ms=latency_ms
                )

                summary_parts = []
                if title:
                    summary_parts.append(f"Title: '{title}'")
                all_tech = tech_info.technologies + tech_info.frameworks
                if all_tech:
                    summary_parts.append(f"Stack: {', '.join(all_tech)}")
                if tech_info.waf_or_protection:
                    summary_parts.append(f"Protected by {tech_info.waf_or_protection}")
                if tech_info.has_public_api:
                    summary_parts.append("Exposes JSON/API endpoints")
                if tech_info.pain_points:
                    summary_parts.append(f"Pain points: {'; '.join(tech_info.pain_points)}")

                summary = " | ".join(summary_parts) if summary_parts else f"Online (HTTP {status}, {latency_ms}ms)"

                return TargetInspectionResult(
                    url=url,
                    is_accessible=status < 400,
                    status_code=status,
                    latency_ms=latency_ms,
                    page_title=title,
                    tech_info=tech_info,
                    ground_truth_summary=summary
                )

        except Exception as e:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            return TargetInspectionResult(
                url=url,
                is_accessible=False,
                status_code=0,
                latency_ms=latency_ms,
                ground_truth_summary=f"Inaccessible / Connection error: {str(e)[:100]}"
            )

    async def probe_job(self, job: RawJobPosting) -> TargetInspectionResult:
        """
        Extracts ground truth for a job posting.
        Probes the primary target URL if available, otherwise returns baseline context.
        """
        if job.target_urls:
            primary_url = job.target_urls[0]
            return await self.probe_url(primary_url)

        return TargetInspectionResult(
            url="",
            is_accessible=False,
            status_code=0,
            ground_truth_summary="No external target URL detected in project description; standard description context applies."
        )
