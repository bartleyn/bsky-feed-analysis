"""Streamlit dashboard for Bluesky feed toxicity analysis."""

import streamlit as st

from .analyzer import FeedAnalyzer
from .toxicity_client import ToxicityClient
from .config import TOXICITY_API_URL


st.set_page_config(
    page_title="Bluesky Feed Toxicity Analyzer",
    page_icon="🦋",
    layout="wide",
)

st.title("Bluesky Feed Toxicity Analyzer")


@st.cache_resource
def get_analyzer():
    """Get or create the analyzer instance."""
    return FeedAnalyzer()


def check_toxicity_api():
    """Check if toxicity API is available."""
    client = ToxicityClient()
    return client.health_check()


# Sidebar for configuration
with st.sidebar:
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

# Tabs for different views
tab_discover, tab_analyze = st.tabs(["Discover Feeds", "Analyze Toxicity"])

# Feed Discovery Tab
with tab_discover:
    st.header("Suggested Feeds")

    if st.button("Load Feeds", key="load_feeds"):
        with st.spinner("Fetching feeds from Bluesky..."):
            try:
                analyzer = get_analyzer()
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
                    analyzer = get_analyzer()

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
                except Exception as e:
                    st.error(f"Error during analysis: {e}")

        # Display results
        if "results" in st.session_state and st.session_state.results:
            results = st.session_state.results

            st.subheader("Results")

            # Summary metrics
            total_posts = sum(r.posts_analyzed for r in results)
            total_toxic = sum(r.toxic_count for r in results)
            avg_rate = (total_toxic / total_posts * 100) if total_posts > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Feeds Analyzed", len(results))
            col2.metric("Total Posts", total_posts)
            col3.metric("Overall Toxicity Rate", f"{avg_rate:.1f}%")

            st.divider()

            # Bar chart of toxicity rates
            chart_data = {
                "Feed": [r.feed.name[:20] for r in results],
                "Toxicity Rate (%)": [r.toxicity_rate for r in results],
            }
            st.bar_chart(chart_data, x="Feed", y="Toxicity Rate (%)")

            st.divider()

            # Detailed results per feed
            st.subheader("Feed Details")

            for result in sorted(results, key=lambda r: r.toxicity_rate, reverse=True):
                with st.expander(
                    f"{result.feed.name} - {result.toxicity_rate:.1f}% toxic "
                    f"({result.toxic_count}/{result.posts_analyzed} posts)"
                ):
                    st.caption(f"Average toxicity score: {result.avg_toxicity_score:.3f}")
                    st.caption(f"Creator: {result.feed.creator_handle}")

                    if result.toxic_posts:
                        st.markdown("**Toxic posts:**")
                        for i, tp in enumerate(result.toxic_posts[:10]):
                            st.markdown(
                                f"**@{tp.post.author_handle}** (score: {tp.toxicity.score:.2f})"
                            )
                            st.text(tp.post.text[:500])
                            if i < len(result.toxic_posts) - 1 and i < 9:
                                st.divider()

                        if len(result.toxic_posts) > 10:
                            st.caption(f"... and {len(result.toxic_posts) - 10} more")
                    else:
                        st.success("No toxic posts detected!")
