"""CSV persistence for labeled posts."""

from __future__ import annotations

import csv
import os
from pathlib import Path

from .models import LabeledPost

FIELDNAMES = [
    "uri",
    "text",
    "author_handle",
    "created_at",
    "feed_uri",
    "feed_name",
    "toxicity_score",
    "toxicity_label",
    "sentiment_score",
    "hatespeech_score",
    "corrected_toxicity_label",
    "corrected_hatespeech_label",
    "tags",
    "labeled_at",
]

DEFAULT_FILEPATH = "labeled_posts.csv"


def save_labeled_post(post: LabeledPost, filepath: str = DEFAULT_FILEPATH) -> None:
    """Append a labeled post to the CSV file. Creates the file with headers if needed."""
    file_exists = Path(filepath).exists()
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        row = {
            "uri": post.uri,
            "text": post.text,
            "author_handle": post.author_handle,
            "created_at": post.created_at,
            "feed_uri": post.feed_uri,
            "feed_name": post.feed_name,
            "toxicity_score": post.toxicity_score,
            "toxicity_label": post.toxicity_label,
            "sentiment_score": post.sentiment_score,
            "hatespeech_score": post.hatespeech_score,
            "corrected_toxicity_label": post.corrected_toxicity_label if post.corrected_toxicity_label is not None else "",
            "corrected_hatespeech_label": post.corrected_hatespeech_label if post.corrected_hatespeech_label is not None else "",
            "tags": post.tags,
            "labeled_at": post.labeled_at,
        }
        writer.writerow(row)


def load_labeled_posts(filepath: str = DEFAULT_FILEPATH) -> list[LabeledPost]:
    """Read all labeled posts from the CSV file."""
    if not Path(filepath).exists():
        return []

    posts = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            posts.append(
                LabeledPost(
                    uri=row["uri"],
                    text=row["text"],
                    author_handle=row["author_handle"],
                    created_at=row["created_at"],
                    feed_uri=row["feed_uri"],
                    feed_name=row["feed_name"],
                    toxicity_score=float(row["toxicity_score"]),
                    toxicity_label=int(row["toxicity_label"]),
                    sentiment_score=float(row["sentiment_score"]),
                    hatespeech_score=float(row["hatespeech_score"]),
                    corrected_toxicity_label=int(row["corrected_toxicity_label"]) if row["corrected_toxicity_label"] else None,
                    corrected_hatespeech_label=int(row["corrected_hatespeech_label"]) if row["corrected_hatespeech_label"] else None,
                    tags=row["tags"],
                    labeled_at=row["labeled_at"],
                )
            )
    return posts


def get_labeled_uris(filepath: str = DEFAULT_FILEPATH) -> set[str]:
    """Get the set of URIs that have already been labeled."""
    if not Path(filepath).exists():
        return set()

    uris = set()
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uris.add(row["uri"])
    return uris
