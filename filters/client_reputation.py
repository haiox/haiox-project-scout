"""
Haiox Project Scout - Client Reputation & Freshness Guard
Module: filters/client_reputation.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import time
from typing import Tuple, Optional
from core.schemas import RawJobPosting, UserFilterCriteria


class ClientReputationGuard:
    """
    Evaluates client reliability indicators:
    - Payment method verification status
    - Historic client feedback rating
    - Project posting freshness
    """

    def evaluate(self, job: RawJobPosting, criteria: UserFilterCriteria) -> Tuple[bool, float, Optional[str]]:
        """
        Evaluates client reputation and post age.
        Returns:
            - passed: bool
            - trust_score: float (0.0 to 1.0)
            - reason: Optional rejection reason if rejected, or None if passed
        """
        # 1. Payment Verification Check
        if criteria.payment_verified_only and not job.payment_verified:
            return False, 0.0, "Client payment method is unverified (payment_verified_only is active)"

        # 2. Client Rating Threshold Check
        if criteria.min_client_rating > 0:
            if job.client_rating > 0 and job.client_rating < criteria.min_client_rating:
                return False, 0.0, f"Client rating ({job.client_rating}) is below threshold ({criteria.min_client_rating})"

        # 3. Post Freshness Check
        if criteria.max_age_minutes is not None:
            age_minutes = (time.time() - job.published_at) / 60.0
            if age_minutes > criteria.max_age_minutes:
                return False, 0.0, f"Project age ({round(age_minutes, 1)}m) exceeds maximum age ({criteria.max_age_minutes}m)"

        # Calculate Trust Score (0.0 to 1.0)
        score = 0.5  # Base score
        if job.payment_verified:
            score += 0.25
        if job.client_rating >= 4.5:
            score += 0.25
        elif job.client_rating >= 4.0:
            score += 0.15
        elif job.client_rating > 0:
            score += 0.05

        return True, min(round(score, 2), 1.0), None
