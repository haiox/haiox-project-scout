"""
Haiox Project Scout - Keyword Matcher & Technical Alignment
Module: filters/keyword_matcher.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import re
from typing import List, Tuple, Optional
from core.schemas import RawJobPosting, UserFilterCriteria


class KeywordMatcher:
    """
    Analyzes project titles, descriptions, and skill tags against user keyword criteria.
    Supports boundary-aware matching and negative keyword filtering.
    """

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r'\s+', ' ', text.strip().lower())

    def _matches_keyword(self, text: str, keyword: str) -> bool:
        """Performs word-boundary or flexible token matching."""
        kw = keyword.strip().lower()
        if not kw:
            return False
        # If keyword contains special characters or spaces, use substring
        if re.search(r'[^a-zA-Z0-9]', kw):
            return kw in text
        # Otherwise use word boundary regex to avoid partial false positives
        pattern = rf'\b{re.escape(kw)}\b'
        return bool(re.search(pattern, text))

    def evaluate(self, job: RawJobPosting, criteria: UserFilterCriteria, require_all: bool = False) -> Tuple[bool, float, Optional[str]]:
        """
        Evaluates keyword criteria.
        Returns:
            - passed: bool
            - relevance_score: float (0.0 to 1.0)
            - reason: Optional rejection reason if rejected, or None if passed
        """
        corpus = self._normalize_text(
            f"{job.title} {job.description} {' '.join(job.skills)}"
        )

        # 1. Excluded / Negative Keywords Check
        if criteria.excluded_keywords:
            for bad_kw in criteria.excluded_keywords:
                if self._matches_keyword(corpus, bad_kw):
                    return False, 0.0, f"Excluded keyword detected: '{bad_kw}'"

        # 2. Required Keywords Check
        if criteria.required_keywords:
            matched_count = 0
            for req_kw in criteria.required_keywords:
                if self._matches_keyword(corpus, req_kw):
                    matched_count += 1

            if require_all:
                if matched_count < len(criteria.required_keywords):
                    return False, 0.0, f"Missing required keywords (matched {matched_count}/{len(criteria.required_keywords)})"
            else:
                if matched_count == 0:
                    return False, 0.0, f"None of the required keywords matched: {criteria.required_keywords}"

            relevance = matched_count / len(criteria.required_keywords)
            return True, relevance, None

        # If no required keywords specified, neutral 1.0 relevance
        return True, 1.0, None
