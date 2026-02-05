"""Configuration for the feed analyzer."""

from __future__ import annotations

import os


BLUESKY_PUBLIC_API = "https://public.api.bsky.app"

TOXICITY_API_URL = os.environ.get("TOXICITY_API_URL", "http://localhost:8000")

BSKY_USERNAME = os.environ.get("BSKY_USERNAME", "")
BSKY_APP_PASSWORD = os.environ.get("BSKY_APP_PASSWORD", "")

DEFAULT_TOXICITY_THRESHOLD = 0.5

DEFAULT_NUM_FEEDS = 5

DEFAULT_MAX_POSTS = 100
