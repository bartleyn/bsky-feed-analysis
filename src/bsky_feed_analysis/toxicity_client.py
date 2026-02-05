"""Client for the toxicity scoring API."""

from __future__ import annotations

import httpx

from .config import TOXICITY_API_URL, DEFAULT_TOXICITY_THRESHOLD
from .models import ToxicityResult


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
            ToxicityResult(score=item["score"], label=item["label"])
            for item in data["results"]
        ]

    def health_check(self) -> bool:
        """Check if the toxicity API is available."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except httpx.HTTPError:
            return False
