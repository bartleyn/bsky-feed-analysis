"""Client for the Bluesky API."""

from __future__ import annotations

from datetime import datetime

from atproto import Client

from .config import BLUESKY_PUBLIC_API
from .models import Feed, Post


class BlueskyClient:
    """Client for fetching Bluesky feeds and posts."""

    def __init__(self, base_url: str = BLUESKY_PUBLIC_API):
        self.client = Client(base_url=base_url)

    def get_suggested_feeds(self, limit: int = 20) -> list[Feed]:
        """Get suggested/popular feeds.

        Args:
            limit: Maximum number of feeds to return.

        Returns:
            List of Feed objects.
        """
        response = self.client.app.bsky.feed.get_suggested_feeds({"limit": limit})

        feeds = []
        for feed_view in response.feeds:
            creator_handle = ""
            if hasattr(feed_view, "creator") and feed_view.creator:
                creator_handle = getattr(feed_view.creator, "handle", "")

            feeds.append(
                Feed(
                    uri=feed_view.uri,
                    name=feed_view.display_name or "",
                    description=feed_view.description or "",
                    creator_handle=creator_handle,
                    like_count=feed_view.like_count or 0,
                )
            )

        return feeds

    def get_feed_posts(
        self, feed_uri: str, limit: int = 100, cursor: str | None = None
    ) -> tuple[list[Post], str | None]:
        """Get posts from a feed.

        Args:
            feed_uri: The AT URI of the feed generator.
            limit: Maximum posts to fetch (max 100 per request).
            cursor: Pagination cursor for fetching more posts.

        Returns:
            Tuple of (posts, next_cursor).
        """
        params = {"feed": feed_uri, "limit": min(limit, 100)}
        if cursor:
            params["cursor"] = cursor

        response = self.client.app.bsky.feed.get_feed(params)

        posts = []
        for feed_item in response.feed:
            post_record = feed_item.post

            text = ""
            if hasattr(post_record, "record") and post_record.record:
                text = getattr(post_record.record, "text", "")

            author_handle = ""
            if hasattr(post_record, "author") and post_record.author:
                author_handle = getattr(post_record.author, "handle", "")

            created_at = None
            if hasattr(post_record, "record") and post_record.record:
                created_str = getattr(post_record.record, "created_at", None)
                if created_str:
                    try:
                        created_at = datetime.fromisoformat(
                            created_str.replace("Z", "+00:00")
                        )
                    except (ValueError, AttributeError):
                        pass

            if text:
                posts.append(
                    Post(
                        uri=post_record.uri,
                        text=text,
                        author_handle=author_handle,
                        created_at=created_at,
                    )
                )

        return posts, response.cursor

    def get_feed_posts_all(self, feed_uri: str, max_posts: int = 100) -> list[Post]:
        """Get posts from a feed, handling pagination.

        Args:
            feed_uri: The AT URI of the feed generator.
            max_posts: Maximum total posts to fetch.

        Returns:
            List of Post objects.
        """
        all_posts = []
        cursor = None

        while len(all_posts) < max_posts:
            remaining = max_posts - len(all_posts)
            batch_size = min(remaining, 100)

            posts, cursor = self.get_feed_posts(
                feed_uri, limit=batch_size, cursor=cursor
            )
            all_posts.extend(posts)

            if not cursor or not posts:
                break

        return all_posts[:max_posts]
