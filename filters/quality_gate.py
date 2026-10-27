"""
Haiox Project Scout - Unified Quality Gatekeeper
Module: filters/quality_gate.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from core.schemas import RawJobPosting, UserFilterCriteria
from .price_guard import PriceGuard, CurrencyConverter
from .keyword_matcher import KeywordMatcher
from .client_reputation import ClientReputationGuard


@dataclass
class FilterDecision:
    """Consolidated outcome of the quality gate evaluation."""
    job_id: str
    passed: bool
    overall_score: float  # 0.0 to 100.0
    normalized_usd_price: float
    reasons: List[str] = field(default_factory=list)
    has_target_urls: bool = False
    target_urls_count: int = 0
    breakdown: Dict[str, float] = field(default_factory=dict)


class QualityGate:
    """
    Central gatekeeper orchestrating multi-factor filtering:
    - Anti-Phishing Guard (detects off-platform steering, numbers, telegram/whatsapp)
    - PriceGuard (Economic viability & Currency normalization)
    - KeywordMatcher (Technical alignment & Negative filters)
    - ClientReputationGuard (Trust & Freshness)
    - Ground Truth Opportunity (Presence of actionable Target URLs)
    """

    PHONE_PATTERN = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
    OFF_PLATFORM_KEYWORDS = ["whatsapp", "telegram", "text me", "call me", "signal me", "send me a note("]

    def __init__(
        self,
        price_guard: Optional[PriceGuard] = None,
        keyword_matcher: Optional[KeywordMatcher] = None,
        reputation_guard: Optional[ClientReputationGuard] = None,
        strict_anti_phishing: bool = True
    ):
        self.price_guard = price_guard or PriceGuard()
        self.keyword_matcher = keyword_matcher or KeywordMatcher()
        self.reputation_guard = reputation_guard or ClientReputationGuard()
        self.strict_anti_phishing = strict_anti_phishing

    def evaluate(self, job: RawJobPosting, criteria: UserFilterCriteria) -> FilterDecision:
        """
        Runs comprehensive checks on a job posting against user criteria.
        Returns a FilterDecision with passed/rejected status and overall quality score.
        """
        rejection_reasons: List[str] = []
        positive_notes: List[str] = []

        corpus = f"{job.title} {job.description}".lower()

        # 0. Anti-Phishing & Off-Platform Guard
        if self.strict_anti_phishing:
            if self.PHONE_PATTERN.search(job.description):
                return FilterDecision(
                    job_id=job.id,
                    passed=False,
                    overall_score=0.0,
                    normalized_usd_price=0.0,
                    reasons=["Rejected by Anti-Phishing: Hidden phone number pattern detected in description."]
                )
            for bad_off in self.OFF_PLATFORM_KEYWORDS:
                if bad_off in corpus:
                    return FilterDecision(
                        job_id=job.id,
                        passed=False,
                        overall_score=0.0,
                        normalized_usd_price=0.0,
                        reasons=[f"Rejected by Anti-Phishing: Off-platform keyword '{bad_off}' detected."]
                    )

        # 1. Price Evaluation
        price_passed, usd_price, price_reason = self.price_guard.evaluate(job, criteria)
        if not price_passed:
            rejection_reasons.append(price_reason or "Price criteria violated")
        else:
            positive_notes.append(f"Price verified (${usd_price} USD equivalent)")

        # 2. Keyword Evaluation
        kw_passed, kw_score, kw_reason = self.keyword_matcher.evaluate(job, criteria)
        if not kw_passed:
            rejection_reasons.append(kw_reason or "Keyword criteria violated")
        else:
            positive_notes.append(f"Technical keyword alignment: {int(kw_score * 100)}%")

        # 3. Reputation & Freshness Evaluation
        rep_passed, rep_score, rep_reason = self.reputation_guard.evaluate(job, criteria)
        if not rep_passed:
            rejection_reasons.append(rep_reason or "Client reputation criteria violated")
        else:
            positive_notes.append(f"Client trust rating: {int(rep_score * 100)}%")

        # Final Pass / Reject decision
        passed = price_passed and kw_passed and rep_passed

        # Ground Truth Opportunity (Target URLs)
        has_targets = len(job.target_urls) > 0
        target_bonus = 15.0 if has_targets else 0.0
        if has_targets:
            positive_notes.append(f"Target URLs detected for Smart Miner inspection: {len(job.target_urls)}")

        # Score computation (0 - 100)
        price_subscore = 15.0 if (price_passed and usd_price > 0) else 10.0
        kw_subscore = kw_score * 40.0
        rep_subscore = rep_score * 30.0

        raw_score = price_subscore + kw_subscore + rep_subscore + target_bonus
        final_score = round(min(raw_score, 100.0), 1)

        decision_reasons = positive_notes if passed else rejection_reasons

        return FilterDecision(
            job_id=job.id,
            passed=passed,
            overall_score=final_score if passed else 0.0,
            normalized_usd_price=usd_price,
            reasons=decision_reasons,
            has_target_urls=has_targets,
            target_urls_count=len(job.target_urls),
            breakdown={
                "price_score": price_subscore,
                "keyword_score": kw_subscore,
                "reputation_score": rep_subscore,
                "target_bonus": target_bonus,
            }
        )
