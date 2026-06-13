"""Fallback policy analyzer used by policy_analysis.py.

This keeps the research agent running when the vendored
AI-Policy-Terms-Analyzer module is unavailable or incomplete.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PolicyResult:
    compliant: bool
    score: float
    notes: str


class PolicyAnalyzer:
    """Lightweight policy analyzer compatible with policy_analysis.py.

    The surrounding integration expects two methods:
    - analyze(text, company_name=...)
    - generate_user_summary(analysis)

    This implementation uses simple keyword matching so the pipeline can run.
    Replace it later with the full external analyzer if required.
    """

    HIGH_TERMS = (
        "sell personal data",
        "sell your data",
        "share personal data",
        "third-party advertisers",
        "tracking",
        "biometric",
        "precise location",
    )

    MEDIUM_TERMS = (
        "cookies",
        "analytics",
        "third party",
        "third-party",
        "data sharing",
        "personal information",
        "usage data",
        "log data",
    )

    LOW_TERMS = (
        "privacy policy",
        "terms of service",
        "open source",
        "license",
        "readme",
    )

    TECHNOLOGY_TERMS = (
        "openai",
        "github",
        "google analytics",
        "firebase",
        "supabase",
        "stripe",
        "sentry",
        "posthog",
        "mixpanel",
        "aws",
        "azure",
        "cloudflare",
    )

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    def _find_terms(self, text: str, terms: tuple[str, ...]) -> list[str]:
        lower = text.lower()
        return [term for term in terms if term in lower]

    def analyze(self, text: str, company_name: str = "Unknown") -> dict[str, Any]:
        high = self._find_terms(text, self.HIGH_TERMS)
        medium = self._find_terms(text, self.MEDIUM_TERMS)
        low = self._find_terms(text, self.LOW_TERMS)
        technologies = self._find_terms(text, self.TECHNOLOGY_TERMS)

        return {
            "company_name": company_name,
            "privacy_concerns": {
                "high": high,
                "medium": medium,
                "low": low,
            },
            "third_party_services_categorised": {
                "detected": technologies,
            },
            "data_sharing_summary": {
                "shared_with": technologies,
            },
            "technologies_detected": {
                "detected": technologies,
            },
            "compliance_score": max(0.0, 1.0 - (0.2 * len(high)) - (0.05 * len(medium))),
        }

    def analyse(self, text: str, company_name: str = "Unknown") -> dict[str, Any]:
        """Australian/British spelling alias."""
        return self.analyze(text, company_name=company_name)

    def generate_user_summary(self, analysis: dict[str, Any]) -> str:
        concerns = analysis.get("privacy_concerns") or {}
        high = len(concerns.get("high", []) or [])
        medium = len(concerns.get("medium", []) or [])
        low = len(concerns.get("low", []) or [])
        company_name = analysis.get("company_name", "Unknown")

        if high or medium:
            return (
                f"{company_name}: detected {high} high, {medium} medium, "
                f"and {low} low policy/privacy signals in the available README text."
            )

        return (
            f"{company_name}: no strong policy/privacy risks were detected "
            "in the available README text by the fallback analyser."
        )
