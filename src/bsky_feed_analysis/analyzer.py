"""Feed analyzer that orchestrates toxicity analysis."""

from __future__ import annotations

import sys

from .bluesky_client import BlueskyClient
from .toxicity_client import ToxicityClient
from .models import Feed, FeedAnalysisResult, PostWithToxicity
from .config import DEFAULT_NUM_FEEDS, DEFAULT_MAX_POSTS


class FeedAnalyzer:
    """Orchestrates feed discovery and toxicity analysis."""

    def __init__(
        self,
        bluesky_client: BlueskyClient | None = None,
        toxicity_client: ToxicityClient | None = None,
    ):
        self.bluesky = bluesky_client or BlueskyClient()
        self.toxicity = toxicity_client or ToxicityClient()

    def login(self, username: str | None = None, app_password: str | None = None) -> None:
        """Log in to Bluesky for authenticated feed access."""
        self.bluesky.login(username=username, app_password=app_password)

    def list_feeds(self, limit: int = DEFAULT_NUM_FEEDS) -> list[Feed]:
        """Get suggested feeds.

        Args:
            limit: Maximum number of feeds to return.

        Returns:
            List of Feed objects.
        """
        return self.bluesky.get_suggested_feeds(limit=limit)

    def analyze_feed(
        self, feed: Feed, max_posts: int = DEFAULT_MAX_POSTS
    ) -> FeedAnalysisResult:
        """Analyze a single feed for toxicity.

        Args:
            feed: The feed to analyze.
            max_posts: Maximum posts to analyze.

        Returns:
            FeedAnalysisResult with toxicity metrics.
        """
        posts = self.bluesky.get_feed_posts_all(feed.uri, max_posts=max_posts)

        if not posts:
            return FeedAnalysisResult(
                feed=feed,
                posts_analyzed=0,
                toxic_count=0,
                avg_toxicity_score=0.0,
                toxic_posts=[],
            )

        texts = [post.text for post in posts]
        results = self.toxicity.score_texts(texts)

        toxic_posts = []
        total_score = 0.0
        toxic_count = 0

        for post, result in zip(posts, results):
            total_score += result.score
            if result.label == 1:
                toxic_count += 1
                toxic_posts.append(PostWithToxicity(post=post, toxicity=result))

        avg_score = total_score / len(results) if results else 0.0

        return FeedAnalysisResult(
            feed=feed,
            posts_analyzed=len(posts),
            toxic_count=toxic_count,
            avg_toxicity_score=avg_score,
            toxic_posts=toxic_posts,
        )

    def analyze_feeds(
        self,
        num_feeds: int = DEFAULT_NUM_FEEDS,
        max_posts: int = DEFAULT_MAX_POSTS,
        feed_uri: str | None = None,
    ) -> list[FeedAnalysisResult]:
        """Analyze multiple feeds for toxicity.

        Args:
            num_feeds: Number of feeds to analyze (ignored if feed_uri provided).
            max_posts: Maximum posts to analyze per feed.
            feed_uri: Specific feed URI to analyze (optional).

        Returns:
            List of FeedAnalysisResult objects.
        """
        if feed_uri:
            feed = Feed(uri=feed_uri, name="Custom Feed")
            return [self.analyze_feed(feed, max_posts=max_posts)]

        feeds = self.list_feeds(limit=num_feeds)
        results = []

        for feed in feeds:
            try:
                result = self.analyze_feed(feed, max_posts=max_posts)
                results.append(result)
            except Exception as e:
                print(f"Skipping feed '{feed.name}': {e}", file=sys.stderr)

        return results
