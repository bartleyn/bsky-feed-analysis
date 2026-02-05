"""Data models for feed analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Feed:
    """Represents a Bluesky curated feed."""

    uri: str
    name: str
    description: str = ""
    creator_handle: str = ""
    like_count: int = 0


@dataclass
class Post:
    """Represents a Bluesky post."""

    uri: str
    text: str
    author_handle: str
    created_at: datetime | None = None


@dataclass
class ToxicityResult:
    """Result from toxicity analysis of a single text."""

    score: float
    label: int
    sentiment_score: float = 0.0


@dataclass
class PostWithToxicity:
    """A post with its toxicity analysis."""

    post: Post
    toxicity: ToxicityResult


@dataclass
class FeedAnalysisResult:
    """Complete analysis result for a feed."""

    feed: Feed
    posts_analyzed: int
    toxic_count: int
    avg_toxicity_score: float
    avg_sentiment_score: float = 0.0
    toxic_posts: list[PostWithToxicity] = field(default_factory=list)

    @property
    def toxicity_rate(self) -> float:
        """Percentage of posts classified as toxic."""
        if self.posts_analyzed == 0:
            return 0.0
        return (self.toxic_count / self.posts_analyzed) * 100
