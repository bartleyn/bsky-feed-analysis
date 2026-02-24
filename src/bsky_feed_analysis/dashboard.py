"""Streamlit dashboard for Bluesky feed toxicity analysis."""

from datetime import datetime, timezone

import streamlit as st

from bsky_feed_analysis.analyzer import FeedAnalyzer
from bsky_feed_analysis.toxicity_client import ToxicityClient
from bsky_feed_analysis.config import TOXICITY_API_URL, BSKY_USERNAME, BSKY_APP_PASSWORD
from bsky_feed_analysis.models import LabeledPost, PostWithToxicity


st.set_page_config(
    page_title="Bluesky Feed Analysis Tool: Toxicity in Context",
    page_icon="🦋",
    layout="wide",
)

st.title("Bluesky Feed Analysis Tool: Toxicity in Context")


@st.cache_resource
def get_analyzer(username: str = "", app_password: str = ""):
    """Get or create the analyzer instance, optionally authenticated."""
    analyzer = FeedAnalyzer()
    if username and app_password:
        analyzer.login(username=username, app_password=app_password)
    return analyzer


def check_toxicity_api():
    """Check if toxicity API is available."""
    client = ToxicityClient()
    return client.health_check()


def render_post_with_labeling(
    pwt: PostWithToxicity,
    feed_uri: str,
    feed_name: str,
    labeled_uris: set[str],
    key_prefix: str,
    analyzer: "FeedAnalyzer | None" = None,
    all_posts: "list[PostWithToxicity] | None" = None,
):
    """Render a single post with its scores and inline labeling controls."""
    already_labeled = pwt.post.uri in labeled_uris

    label_indicator = " [labeled]" if already_labeled else ""
    st.markdown(
        f"**@{pwt.post.author_handle}**{label_indicator} "
        f"(toxicity: {pwt.toxicity.score:.2f}, "
        f"sentiment: {pwt.toxicity.sentiment_score:+.2f}, "
        f"hate: {pwt.toxicity.hatespeech_score:.2f})"
    )
    st.text(pwt.post.text[:500])

    # Context popover for understanding high-scoring posts
    if analyzer is not None:
        with st.popover("Show Context", use_container_width=True):
            # Thread context: parent posts in the conversation
            st.markdown("**Thread Context**")
            try:
                parents = analyzer.bluesky.get_post_thread(pwt.post.uri)
            except Exception:
                parents = []

            if parents:
                for pi, parent in enumerate(parents):
                    st.markdown(
                        f"> **@{parent.author_handle}**: "
                        f"{parent.text[:300]}"
                    )
                    if pi < len(parents) - 1:
                        st.markdown("&nbsp;", unsafe_allow_html=True)
                st.divider()
                st.markdown(
                    f":arrow_right: **@{pwt.post.author_handle}** (this post): "
                    f"{pwt.post.text[:300]}"
                )
            else:
                st.caption("No parent posts (this is a top-level post).")

            # Surrounding feed posts
            if all_posts:
                st.divider()
                st.markdown("**Surrounding Feed Posts**")
                idx = next(
                    (i for i, p in enumerate(all_posts) if p.post.uri == pwt.post.uri),
                    None,
                )
                if idx is not None:
                    start = max(0, idx - 2)
                    end = min(len(all_posts), idx + 3)
                    for i in range(start, end):
                        neighbor = all_posts[i]
                        is_current = i == idx
                        if is_current:
                            st.markdown(
                                f":arrow_right: **@{neighbor.post.author_handle} "
                                f"(THIS POST)** — "
                                f"tox: {neighbor.toxicity.score:.2f}, "
                                f"hate: {neighbor.toxicity.hatespeech_score:.2f}"
                            )
                            st.text(neighbor.post.text[:200])
                        else:
                            st.caption(
                                f"@{neighbor.post.author_handle} — "
                                f"tox: {neighbor.toxicity.score:.2f}, "
                                f"hate: {neighbor.toxicity.hatespeech_score:.2f}"
                            )
                            st.caption(neighbor.post.text[:200])
                        if i < end - 1:
                            st.divider()

            # Author's recent posts (non-threaded sequential context)
            st.divider()
            st.markdown("**Author's Recent Posts**")
            try:
                author_posts = analyzer.bluesky.get_author_feed(
                    pwt.post.author_handle, limit=10
                )
            except Exception:
                author_posts = []

            if author_posts:
                # Find this post in the author's timeline and show nearby posts
                author_idx = next(
                    (i for i, p in enumerate(author_posts) if p.uri == pwt.post.uri),
                    None,
                )
                if author_idx is not None:
                    start = max(0, author_idx - 3)
                    end = min(len(author_posts), author_idx + 4)
                    # Author feed is newest-first; reverse slice for chronological order
                    window = list(range(start, end))
                    for wi, i in enumerate(window):
                        ap = author_posts[i]
                        is_current = i == author_idx
                        if is_current:
                            st.markdown(
                                f":arrow_right: **@{ap.author_handle} "
                                f"(THIS POST)**"
                            )
                            st.text(ap.text[:200])
                        else:
                            st.caption(f"@{ap.author_handle}")
                            st.caption(ap.text[:200])
                        if wi < len(window) - 1:
                            st.divider()
                else:
                    # Post not in recent 10; just show the latest posts for context
                    st.caption(
                        f"Recent posts by @{pwt.post.author_handle} "
                        f"(scored post not in latest 10):"
                    )
                    for wi, ap in enumerate(reversed(author_posts[:5])):
                        st.caption(f"@{ap.author_handle}: {ap.text[:200]}")
                        if wi < min(len(author_posts), 5) - 1:
                            st.divider()
            else:
                st.caption("Could not fetch author's recent posts.")

    with st.popover("Label this post", use_container_width=True):
        tox_options = ["No correction", "Toxic", "Not toxic"]
        tox_choice = st.selectbox(
            "Toxicity correction",
            tox_options,
            key=f"{key_prefix}_tox",
        )

        hate_options = ["No correction", "Hate speech", "Not hate speech"]
        hate_choice = st.selectbox(
            "Hate speech correction",
            hate_options,
            key=f"{key_prefix}_hate",
        )

        tags = st.text_input(
            "Tags (comma-separated)",
            key=f"{key_prefix}_tags",
            placeholder="sarcasm, false-positive, political",
        )

        if st.button("Save Label", key=f"{key_prefix}_save"):
            corrected_tox = None
            if tox_choice == "Toxic":
                corrected_tox = 1
            elif tox_choice == "Not toxic":
                corrected_tox = 0

            corrected_hate = None
            if hate_choice == "Hate speech":
                corrected_hate = 1
            elif hate_choice == "Not hate speech":
                corrected_hate = 0

            labeled = LabeledPost(
                uri=pwt.post.uri,
                text=pwt.post.text,
                author_handle=pwt.post.author_handle,
                created_at=str(pwt.post.created_at) if pwt.post.created_at else "",
                feed_uri=feed_uri,
                feed_name=feed_name,
                toxicity_score=pwt.toxicity.score,
                toxicity_label=pwt.toxicity.label,
                sentiment_score=pwt.toxicity.sentiment_score,
                hatespeech_score=pwt.toxicity.hatespeech_score,
                corrected_toxicity_label=corrected_tox,
                corrected_hatespeech_label=corrected_hate,
                tags=tags.strip(),
                labeled_at=datetime.now(timezone.utc).isoformat(),
            )
            try:
                toxicity_client = ToxicityClient()
                toxicity_client.submit_label(labeled)
                st.session_state["labeled_uris"].add(pwt.post.uri)
                st.success("Label sent to API!")
            except Exception as e:
                st.error(f"Failed to submit label: {e}")


# Sidebar for configuration
with st.sidebar:
    st.header("Bluesky Login")
    if st.session_state.get("bsky_logged_in"):
        st.success(f"Logged in as {st.session_state['bsky_user']}")
        bsky_user = st.session_state["bsky_user"]
        bsky_pass = st.session_state["bsky_pass"]
    else:
        bsky_user = st.text_input(
            "Username / handle",
            value=BSKY_USERNAME,
            placeholder="you.bsky.social",
        )
        bsky_pass = st.text_input(
            "App password",
            value=BSKY_APP_PASSWORD,
            type="password",
            placeholder="xxxx-xxxx-xxxx-xxxx",
        )
        if bsky_user and bsky_pass:
            try:
                get_analyzer(username=bsky_user, app_password=bsky_pass)
                st.session_state["bsky_logged_in"] = True
                st.session_state["bsky_user"] = bsky_user
                st.session_state["bsky_pass"] = bsky_pass
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")
        else:
            st.info("Log in for full feed access (some feeds require auth)")

    st.divider()
    st.header("Configuration")
    st.text(f"Toxicity API: {TOXICITY_API_URL}")

    if check_toxicity_api():
        st.success("Toxicity API: Connected")
    else:
        st.error("Toxicity API: Not available")
        st.caption("Start the toxicity API or set TOXICITY_API_URL")

    st.divider()
    max_posts = st.slider("Max posts per feed", 10, 200, 50, step=10)
    num_feeds = st.slider("Number of feeds to analyze", 1, 20, 5)

    # Label management section
    st.divider()
    st.header("Labels")

    if "labeled_uris" not in st.session_state:
        st.session_state["labeled_uris"] = set()

    st.metric("Labeled Posts (this session)", len(st.session_state["labeled_uris"]))

# Tabs for different views
tab_discover, tab_analyze = st.tabs(["Discover Feeds", "Analyze Toxicity"])

# Feed Discovery Tab
with tab_discover:
    st.header("Suggested Feeds")

    if st.button("Load Feeds", key="load_feeds"):
        with st.spinner("Fetching feeds from Bluesky..."):
            try:
                analyzer = get_analyzer(username=bsky_user, app_password=bsky_pass)
                feeds = analyzer.list_feeds(limit=20)
                st.session_state.feeds = feeds
            except Exception as e:
                st.error(f"Error fetching feeds: {e}")

    if "feeds" in st.session_state and st.session_state.feeds:
        feeds = st.session_state.feeds

        # Display as table
        feed_data = [
            {
                "Name": f.name,
                "Creator": f.creator_handle,
                "Likes": f.like_count,
                "Description": f.description[:100] + "..." if len(f.description) > 100 else f.description,
            }
            for f in feeds
        ]
        st.dataframe(feed_data, use_container_width=True)

# Analysis Tab
with tab_analyze:
    st.header("Toxicity Analysis")

    if not check_toxicity_api():
        st.warning("Toxicity API is not available. Please start it first.")
    else:
        col1, col2 = st.columns([2, 1])

        with col1:
            analyze_mode = st.radio(
                "Analysis mode",
                ["Suggested feeds", "Specific feed URI"],
                horizontal=True,
            )

        specific_uri = None
        if analyze_mode == "Specific feed URI":
            specific_uri = st.text_input(
                "Feed URI",
                placeholder="at://did:plc:.../app.bsky.feed.generator/...",
            )

        if st.button("Run Analysis", type="primary"):
            with st.spinner("Analyzing feeds..."):
                try:
                    analyzer = get_analyzer(username=bsky_user, app_password=bsky_pass)

                    if specific_uri:
                        results = analyzer.analyze_feeds(
                            feed_uri=specific_uri,
                            max_posts=max_posts,
                        )
                    else:
                        results = analyzer.analyze_feeds(
                            num_feeds=num_feeds,
                            max_posts=max_posts,
                        )

                    st.session_state.results = results
                    st.session_state["labeled_uris"] = set()
                except Exception as e:
                    st.error(f"Error during analysis: {e}")

        # Display results
        if "results" in st.session_state and st.session_state.results:
            results = st.session_state.results

            st.subheader("Results")

            # Summary metrics
            total_posts = sum(r.posts_analyzed for r in results)
            total_toxic = sum(r.toxic_count for r in results)
            total_high_hate = sum(r.high_hate_count for r in results)
            avg_rate = (total_toxic / total_posts * 100) if total_posts > 0 else 0
            high_hate_rate = (total_high_hate / total_posts * 100) if total_posts > 0 else 0

            avg_sentiment = (
                sum(r.avg_sentiment_score * r.posts_analyzed for r in results) / total_posts
                if total_posts > 0 else 0
            )

            avg_hate = (
                sum(r.avg_hatespeech_score * r.posts_analyzed for r in results) / total_posts
                if total_posts > 0 else 0
            )

            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("Feeds Analyzed", len(results))
            col2.metric("Total Posts", total_posts)
            col3.metric("Toxicity Rate", f"{avg_rate:.1f}%")
            col4.metric("High Hate Rate", f"{high_hate_rate:.1f}%")
            col5.metric("Avg Sentiment", f"{avg_sentiment:+.3f}")
            col6.metric("Avg Hate Score", f"{avg_hate:.3f}")

            st.divider()

            # Bar chart of toxicity rates
            chart_data = {
                "Feed": [r.feed.name[:20] for r in results],
                "Toxicity Rate (%)": [r.toxicity_rate for r in results],
                "High Hate Rate (%)": [r.high_hate_rate for r in results],
                "Avg Sentiment": [r.avg_sentiment_score for r in results],
                "Avg Hate Speech": [r.avg_hatespeech_score for r in results],
            }
            st.bar_chart(chart_data, x="Feed", y=["Toxicity Rate (%)", "High Hate Rate (%)"])

            st.bar_chart(chart_data, x="Feed", y="Avg Sentiment")

            st.bar_chart(chart_data, x="Feed", y="Avg Hate Speech")

            st.divider()

            # Detailed results per feed
            st.subheader("Feed Details")

            labeled_uris = st.session_state.get("labeled_uris", set())
            current_analyzer = get_analyzer(username=bsky_user, app_password=bsky_pass)

            for ri, result in enumerate(sorted(results, key=lambda r: r.toxicity_rate, reverse=True)):
                with st.expander(
                    f"{result.feed.name} - {result.toxicity_rate:.1f}% toxic, "
                    f"{result.high_hate_rate:.1f}% high hate "
                    f"({result.posts_analyzed} posts)"
                ):
                    st.caption(f"Average toxicity score: {result.avg_toxicity_score:.3f}")
                    st.caption(f"Average sentiment: {result.avg_sentiment_score:+.3f}")
                    st.caption(f"Average hate speech score: {result.avg_hatespeech_score:.3f}")
                    st.caption(f"Creator: {result.feed.creator_handle}")

                    post_tab_toxic, post_tab_hate, post_tab_all = st.tabs(
                        [
                            f"Toxic Posts ({result.toxic_count})",
                            f"High Hate Posts ({result.high_hate_count})",
                            f"All Posts ({result.posts_analyzed})",
                        ]
                    )

                    with post_tab_toxic:
                        if result.toxic_posts:
                            for i, tp in enumerate(result.toxic_posts[:10]):
                                render_post_with_labeling(
                                    tp,
                                    feed_uri=result.feed.uri,
                                    feed_name=result.feed.name,
                                    labeled_uris=labeled_uris,
                                    key_prefix=f"toxic_{ri}_{i}",
                                    analyzer=current_analyzer,
                                    all_posts=result.all_posts,
                                )
                                if i < len(result.toxic_posts) - 1 and i < 9:
                                    st.divider()

                            if len(result.toxic_posts) > 10:
                                st.caption(f"... and {len(result.toxic_posts) - 10} more")
                        else:
                            st.success("No toxic posts detected!")

                    with post_tab_hate:
                        if result.high_hate_posts:
                            sorted_hate = sorted(
                                result.high_hate_posts,
                                key=lambda x: x.toxicity.hatespeech_score,
                                reverse=True,
                            )
                            for i, hp in enumerate(sorted_hate[:10]):
                                render_post_with_labeling(
                                    hp,
                                    feed_uri=result.feed.uri,
                                    feed_name=result.feed.name,
                                    labeled_uris=labeled_uris,
                                    key_prefix=f"hate_{ri}_{i}",
                                    analyzer=current_analyzer,
                                    all_posts=result.all_posts,
                                )
                                if i < len(result.high_hate_posts) - 1 and i < 9:
                                    st.divider()

                            if len(result.high_hate_posts) > 10:
                                st.caption(f"... and {len(result.high_hate_posts) - 10} more")
                        else:
                            st.success("No high hate speech posts detected!")

                    with post_tab_all:
                        if result.all_posts:
                            for i, ap in enumerate(result.all_posts):
                                render_post_with_labeling(
                                    ap,
                                    feed_uri=result.feed.uri,
                                    feed_name=result.feed.name,
                                    labeled_uris=labeled_uris,
                                    key_prefix=f"all_{ri}_{i}",
                                    analyzer=current_analyzer,
                                    all_posts=result.all_posts,
                                )
                                if i < len(result.all_posts) - 1:
                                    st.divider()
                        else:
                            st.info("No posts found in this feed.")
