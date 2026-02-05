# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CLI tool that discovers Bluesky curated feeds, fetches posts, and analyzes toxicity using a toxicity scoring API.

## Build & Development Commands

```bash
# Install in development mode
pip install -e .

# Run CLI via module
python -m bsky_feed_analysis list-feeds --limit 5
python -m bsky_feed_analysis analyze --num-feeds 3 --max-posts 50

# Run CLI via entry point (after pip install)
bsky-feed-analysis list-feeds
bsky-feed-analysis analyze --json
```

## Environment Variables

- `TOXICITY_API_URL` - URL of toxicity scoring API (default: `http://localhost:8000`)

## Architecture

```
src/bsky_feed_analysis/
├── __init__.py          # Package version
├── __main__.py          # Entry point for python -m
├── cli.py               # Argument parsing and output formatting
├── config.py            # Configuration constants and env vars
├── models.py            # Data classes (Feed, Post, ToxicityResult, etc.)
├── bluesky_client.py    # Bluesky API wrapper using atproto SDK
├── toxicity_client.py   # HTTP client for toxicity scoring API
└── analyzer.py          # Orchestration layer combining clients
```

### Key Components

- **BlueskyClient**: Uses `atproto` SDK to discover feeds (`get_suggested_feeds`) and fetch posts (`get_feed_posts_all`)
- **ToxicityClient**: Calls `/score` endpoint with batch of texts, returns scores and labels
- **FeedAnalyzer**: Orchestrates feed discovery and toxicity analysis, computes aggregate metrics
- **CLI**: Two commands - `list-feeds` for discovery, `analyze` for toxicity analysis

### Dependencies

- `atproto>=0.0.50` - Bluesky AT Protocol SDK
- `httpx>=0.25.0` - HTTP client for toxicity API
