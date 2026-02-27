"""Client for the toxicity scoring API."""

from __future__ import annotations

import httpx

from .config import TOXICITY_API_URL, DEFAULT_TOXICITY_THRESHOLD
from .models import ToxicityResult, LabeledPost, TokenContribution, ExplanationResult


class ToxicityClient:
    """Client for scoring text toxicity."""

    def __init__(
        self,
        base_url: str = TOXICITY_API_URL,
        threshold: float = DEFAULT_TOXICITY_THRESHOLD,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.threshold = threshold
        self.timeout = timeout

    def score_texts(self, texts: list[str]) -> list[ToxicityResult]:
        """Score a batch of texts for toxicity.

        Args:
            texts: List of text strings to analyze.

        Returns:
            List of ToxicityResult objects with scores and labels.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        if not texts:
            return []

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/score",
                json={"texts": texts, "threshold": self.threshold},
            )
            response.raise_for_status()
            data = response.json()

        return [
            ToxicityResult(
                score=item["scores"]["toxicity"],
                label=item["label"],
                sentiment_score=item["scores"].get("sentiment", 0.0),
                hatespeech_score=item["scores"].get("hatespeech", 0.0)
            )
            for item in data["results"]
        ]

    def submit_label(self, labeled_post: LabeledPost) -> dict:
        """Submit a labeled post to the API for storage.

        Args:
            labeled_post: The labeled post with corrections and tags.

        Returns:
            Response data from the API.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        payload = {
            "uri": labeled_post.uri,
            "text": labeled_post.text,
            "author_handle": labeled_post.author_handle,
            "created_at": labeled_post.created_at,
            "feed_uri": labeled_post.feed_uri,
            "feed_name": labeled_post.feed_name,
            "toxicity_score": labeled_post.toxicity_score,
            "toxicity_label": labeled_post.toxicity_label,
            "sentiment_score": labeled_post.sentiment_score,
            "hatespeech_score": labeled_post.hatespeech_score,
            "corrected_toxicity_label": labeled_post.corrected_toxicity_label,
            "corrected_hatespeech_label": labeled_post.corrected_hatespeech_label,
            "tags": labeled_post.tags,
            "labeled_at": labeled_post.labeled_at,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/labels",
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    def explain_text(
        self,
        text: str,
        signal_name: str = "toxicity",
        top_n: int = 10,
    ) -> ExplanationResult:
        """Get SHAP-based explanation for a single text.

        Args:
            text: The text to explain.
            signal_name: Which signal to explain (toxicity, sentiment, hatespeech).
            top_n: Maximum number of token contributions to return.

        Returns:
            ExplanationResult with token-level contributions.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/explain",
                json={"text": text, "signal_name": signal_name, "top_n": top_n},
            )
            response.raise_for_status()
            data = response.json()

        contributions = [
            TokenContribution(token=c["token"], value=c["weight"])
            for c in data["contributions"]
        ]
        return ExplanationResult(
            text=data["text"],
            signal_name=data["signal_name"],
            score=data["score"],
            contributions=contributions,
        )

    def health_check(self) -> bool:
        """Check if the toxicity API is available."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except httpx.HTTPError:
            return False
