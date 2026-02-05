"""Entry point for python -m bsky_feed_analysis."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
