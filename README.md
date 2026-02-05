# bsky-feed-analysis

CLI + web dashboard that pulls posts from Bluesky curated feeds and runs them through a toxicity/sentiment scoring API. You get per-feed toxicity rates, sentiment averages, and can drill into the flagged posts.

## Important Assumption

This tool assumes the underlying toxicity and sentiment models are **well-tuned and unbiased**. It takes the scores at face value. If your models are garbage, your results will be garbage. Make sure you trust what's behind your `/score` endpoint before drawing any conclusions from the output.

## Setup

```bash
pip install -e .
```

You'll need a toxicity/sentiment API running that exposes a `/score` endpoint. The [toxic-cicd](https://github.com/bartleyn/toxic-cicd) project is an example of an API that works with this tool. Point to it with:

```bash
export TOXICITY_API_URL=http://localhost:8000  # default
```

For authenticated Bluesky access (some feeds require it):

```bash
export BSKY_USERNAME=you.bsky.social
export BSKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # generate at Settings > App Passwords
```

## Usage

**List feeds:**
```bash
bsky-feed-analysis list-feeds --limit 10
bsky-feed-analysis --login list-feeds  # authenticated
```

**Run analysis:**
```bash
bsky-feed-analysis analyze --num-feeds 3 --max-posts 50
bsky-feed-analysis analyze --feed-uri at://did:plc:.../app.bsky.feed.generator/...
bsky-feed-analysis analyze --json  # machine-readable output
```

**Web dashboard:**
```bash
streamlit run src/bsky_feed_analysis/dashboard.py
```

The dashboard gives you charts, expandable feed details, and lets you log in to Bluesky directly from the sidebar.
