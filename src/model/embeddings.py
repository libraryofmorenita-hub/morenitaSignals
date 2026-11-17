"""
src/model/embeddings.py

Stage 4b — Model: sentence embeddings
--------------------------------------
TF-IDF only links works that share an exact tag, so "Afrobeat" never meets
"Yoruba". A sentence-transformer reads a short description of each work and
turns it into a vector of *meaning*, so related ideas land close together
even when they share no words.

Run once after the pipeline (first run downloads the model, about 90 MB):
    pip install sentence-transformers
    python -m src.model.embeddings

Saves data/clean/embeddings.npy plus the work keys in the same order, which
the recommender picks up automatically.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

CLEAN_DIR = Path(__file__).resolve().parents[2] / "data" / "clean"
EMB_PATH = CLEAN_DIR / "embeddings.npy"
KEYS_PATH = CLEAN_DIR / "embeddings_keys.json"
MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast, good general-purpose model

KIND = {"book": "A book", "art": "An artwork", "music": "A musician"}


def describe(row: pd.Series) -> str:
    """One plain sentence per work, which is what the model reads."""
    from src.model.recommender import _subjects

    parts = [f"{KIND.get(row.get('domain'), 'A work')}: {row['title']}"]
    if row.get("author_name") and row.get("author_name") != row["title"]:
        parts.append(f"by {row['author_name']}")
    parts.append(f"from the {row.get('collection', '')} collection")
    tags = _subjects(row.get("subject"))[:25]
    if tags:
        parts.append("about " + ", ".join(tags))
    return ". ".join(parts) + "."


def build(df: pd.DataFrame | None = None, model_name: str = MODEL_NAME) -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    if df is None:
        df = pd.read_parquet(CLEAN_DIR / "clean.parquet")
    texts = [describe(r) for _, r in df.iterrows()]
    print(f"Encoding {len(texts)} works with {model_name}...")
    model = SentenceTransformer(model_name)
    vectors = model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    np.save(EMB_PATH, vectors.astype(np.float32))
    KEYS_PATH.write_text(json.dumps(df["key"].tolist()))
    print(f"Saved {vectors.shape} to {EMB_PATH.name}")
    return vectors


def load(keys: list[str]) -> np.ndarray | None:
    """Saved embeddings, or None if missing or out of date with the data."""
    if not (EMB_PATH.exists() and KEYS_PATH.exists()):
        return None
    if json.loads(KEYS_PATH.read_text()) != list(keys):
        print("Embeddings are out of date with the data; run python -m src.model.embeddings")
        return None
    return np.load(EMB_PATH)


if __name__ == "__main__":
    build()
