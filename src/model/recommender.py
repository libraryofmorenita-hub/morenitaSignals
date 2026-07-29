"""
src/model/recommender.py

Stage 4 — Model: TF-IDF Recommendation Engine
-----------------------------------------------
Loads clean data, builds a TF-IDF matrix from subject tags,
computes cosine similarity, and recommends similar books.
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path

CLEAN_DIR = Path(__file__).resolve().parents[2] / "data" / "clean"


def load_data() -> pd.DataFrame:
    return pd.read_parquet(CLEAN_DIR / "clean.parquet")


def build_tfidf_matrix(df: pd.DataFrame):
    df["subject_str"] = df["subject"].apply(
        lambda x: " ".join(x) if hasattr(x, '__iter__') else ""
    )
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(df["subject_str"])
    print(f"Matrix shape: {matrix.shape}")
    return matrix


def build_similarity_matrix(tfidf_matrix):
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    print(f"Similarity matrix shape: {cosine_sim.shape}")
    return cosine_sim


def recommend(title: str, df: pd.DataFrame, cosine_sim, n: int = 5):
    """Return up to n (title, author, score) tuples most similar to `title`."""
    matches = df[df["title"].str.lower() == title.lower()]
    if matches.empty:
        return []

    idx = matches.index[0]
    scores = list(enumerate(cosine_sim[idx]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)[1:n+1]

    return [
        (df["title"].iloc[i], df["author_name"].iloc[i], round(float(score), 3))
        for i, score in scores
    ]


def main():
    df = load_data()
    tfidf_matrix = build_tfidf_matrix(df)
    cosine_sim = build_similarity_matrix(tfidf_matrix)

    for query in ["Blues people", "Ways of Seeing", "Lady sings the blues"]:
        results = recommend(query, df, cosine_sim)
        if not results:
            print(f"Book '{query}' not found.")
            continue
        print(f"\nBooks similar to '{query}':\n")
        for title_, author, score in results:
            print(f"  {title_} — {author} — {score}")


if __name__ == "__main__":
    main()
