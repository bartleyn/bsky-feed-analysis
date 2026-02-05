"""Command-line interface for feed analysis."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from .analyzer import FeedAnalyzer
from .config import DEFAULT_NUM_FEEDS, DEFAULT_MAX_POSTS


def format_feed_table(feeds: list) -> str:
    """Format feeds as a text table."""
    if not feeds:
        return "No feeds found."

    lines = []
    lines.append(f"{'Name':<30} {'Creator':<25} {'Likes':<10}")
    lines.append("-" * 65)

    for feed in feeds:
        name = feed.name[:28] + ".." if len(feed.name) > 30 else feed.name
        creator = (
            feed.creator_handle[:23] + ".."
            if len(feed.creator_handle) > 25
            else feed.creator_handle
        )
        lines.append(f"{name:<30} {creator:<25} {feed.like_count:<10}")

    return "\n".join(lines)


def format_analysis_table(results: list) -> str:
    """Format analysis results as a text table."""
    if not results:
        return "No results."

    lines = []
    lines.append(
        f"{'Feed':<30} {'Posts':<8} {'Toxic':<8} {'Rate':<8} {'Avg Score':<10}"
    )
    lines.append("-" * 70)

    for r in results:
        name = r.feed.name[:28] + ".." if len(r.feed.name) > 30 else r.feed.name
        lines.append(
            f"{name:<30} {r.posts_analyzed:<8} {r.toxic_count:<8} "
            f"{r.toxicity_rate:>6.1f}% {r.avg_toxicity_score:>9.3f}"
        )

    return "\n".join(lines)


def serialize_results(results: list) -> list:
    """Convert results to JSON-serializable format."""
    output = []
    for r in results:
        item = {
            "feed": {
                "uri": r.feed.uri,
                "name": r.feed.name,
                "description": r.feed.description,
                "creator_handle": r.feed.creator_handle,
                "like_count": r.feed.like_count,
            },
            "posts_analyzed": r.posts_analyzed,
            "toxic_count": r.toxic_count,
            "toxicity_rate": r.toxicity_rate,
            "avg_toxicity_score": r.avg_toxicity_score,
            "toxic_posts": [
                {
                    "uri": p.post.uri,
                    "text": p.post.text,
                    "author_handle": p.post.author_handle,
                    "toxicity_score": p.toxicity.score,
                }
                for p in r.toxic_posts
            ],
        }
        output.append(item)
    return output


def _make_analyzer(args: argparse.Namespace) -> FeedAnalyzer:
    """Create an analyzer, optionally logging in."""
    analyzer = FeedAnalyzer()
    if getattr(args, "login", False):
        analyzer.login()
    return analyzer


def cmd_list_feeds(args: argparse.Namespace) -> int:
    """Handle list-feeds command."""
    analyzer = _make_analyzer(args)

    try:
        feeds = analyzer.list_feeds(limit=args.limit)
    except Exception as e:
        print(f"Error fetching feeds: {e}", file=sys.stderr)
        return 1

    if args.json:
        data = [asdict(f) for f in feeds]
        print(json.dumps(data, indent=2))
    else:
        print(format_feed_table(feeds))

    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """Handle analyze command."""
    analyzer = _make_analyzer(args)

    try:
        results = analyzer.analyze_feeds(
            num_feeds=args.num_feeds,
            max_posts=args.max_posts,
            feed_uri=args.feed_uri,
        )
    except Exception as e:
        print(f"Error analyzing feeds: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(serialize_results(results), indent=2))
    else:
        print(format_analysis_table(results))

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="bsky-feed-analysis",
        description="Analyze Bluesky feeds for toxicity",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Log in to Bluesky (requires BSKY_USERNAME and BSKY_APP_PASSWORD env vars)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list-feeds command
    list_parser = subparsers.add_parser("list-feeds", help="List suggested feeds")
    list_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of feeds to list (default: 20)",
    )
    list_parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )

    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze feeds for toxicity")
    analyze_parser.add_argument(
        "--num-feeds",
        type=int,
        default=DEFAULT_NUM_FEEDS,
        help=f"Number of feeds to analyze (default: {DEFAULT_NUM_FEEDS})",
    )
    analyze_parser.add_argument(
        "--max-posts",
        type=int,
        default=DEFAULT_MAX_POSTS,
        help=f"Maximum posts per feed (default: {DEFAULT_MAX_POSTS})",
    )
    analyze_parser.add_argument(
        "--feed-uri",
        type=str,
        help="Analyze a specific feed by AT URI",
    )
    analyze_parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "list-feeds":
        return cmd_list_feeds(args)
    elif args.command == "analyze":
        return cmd_analyze(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())
