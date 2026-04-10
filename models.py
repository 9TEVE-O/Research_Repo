"""Typed dataclasses and schemas for the research agent."""

from dataclasses import dataclass


@dataclass
class ScoredRepo:
    """A GitHub repository that has been scored by the LLM."""

    name: str
    url: str
    relevance_score: int
    summary: str
    reason: str

    def to_dict(self) -> dict:
        """Return a plain dict representation."""
        return {
            "name": self.name,
            "url": self.url,
            "relevance_score": self.relevance_score,
            "summary": self.summary,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScoredRepo":
        """Construct a ScoredRepo from a plain dict."""
        return cls(
            name=data["name"],
            url=data["url"],
            relevance_score=int(data["relevance_score"]),
            summary=data["summary"],
            reason=data["reason"],
        )
