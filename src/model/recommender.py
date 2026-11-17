"""
src/model/recommender.py

Stage 4 — Model: TF-IDF Recommendation Engine
-----------------------------------------------
Loads clean data, builds a TF-IDF matrix from subject tags, and recommends
similar works by cosine similarity.

Two kinds of recommendation:
  - recommend(): the closest works overall ("more like this")
  - bridges():   the closest works from a *different* collection, which is
                 what Signals is for: links across cultures and art forms,
                 e.g. from a jazz history to a book of African literature.

Every result says *why* it matched: the subject tags the two works share.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

CLEAN_DIR = Path(__file__).resolve().parents[2] / "data" / "clean"

# Tags that describe a book's *form* or shelf, not its ideas. Left in, they
# make every biography look like every other biography, and every "history
# and criticism" look alike, which drowns out the cultural links we want.
GENERIC_TAGS = {
    "fiction", "general", "nonfiction", "reference", "literature",
    "history", "history and criticism", "histoire et critique", "geschichte",
    "biography", "juvenile literature", "juvenile fiction", "fiction, general",
    "children's fiction", "translations into english", "criticism and interpretation",
    "accessible book", "protected daisy", "in library", "lending library",
    "large type books", "textbooks", "instruction and study",
}


def _is_generic(tag: str) -> bool:
    t = tag.lower()
    # Bookseller codes like "MUSIC / Classical" or "Genres & Styles - Jazz".
    return t in GENERIC_TAGS or "/" in t or t.startswith(("genres & styles", "biography & autobiography"))


# Below these scores two works aren't really linked. Tag scores run low
# (sharing one rare tag is meaningful); meaning scores run higher for
# everything, so they need a higher bar.
MIN_SCORE = {"tags": 0.08, "meaning": 0.35, "blend": 0.2}
# How "blend" mixes the two: exact shared tags plus similar meaning.
BLEND_TAGS = 0.4


def load_data() -> pd.DataFrame:
    return pd.read_parquet(CLEAN_DIR / "clean.parquet")


def _subjects(value) -> list[str]:
    """Subject tags as a clean list (parquet gives numpy arrays)."""
    if value is None or isinstance(value, str):
        return []
    tags = [str(s).strip() for s in value if str(s).strip()]
    return [t for t in tags if not _is_generic(t)]


@dataclass
class Recommender:
    df: pd.DataFrame
    vectorizer: TfidfVectorizer
    matrix: "np.ndarray"  # sparse, rows L2-normalised
    embeddings: "np.ndarray | None" = None  # dense, rows L2-normalised

    @property
    def default_method(self) -> str:
        return "blend" if self.embeddings is not None else "tags"

    @classmethod
    def build(cls, df: pd.DataFrame | None = None, embeddings: "np.ndarray | None" = None) -> "Recommender":
        df = (load_data() if df is None else df).reset_index(drop=True)
        df["subjects"] = df["subject"].apply(_subjects)
        if "collection" not in df:
            df["collection"] = "unknown"
        if "domain" not in df:
            df["domain"] = "book"
        # Each subject tag ("African American musicians") is one token, so
        # TF-IDF weighs whole ideas, not loose words like "American".
        vectorizer = TfidfVectorizer(
            analyzer=lambda tags: [t.lower() for t in tags],
            min_df=2,
        )
        matrix = normalize(vectorizer.fit_transform(df["subjects"]))
        if embeddings is None:
            from src.model.embeddings import load
            embeddings = load(df["key"].tolist())
        return cls(df=df, vectorizer=vectorizer, matrix=matrix, embeddings=embeddings)

    # ── finding a work ────────────────────────────────────────────────
    def find(self, title: str) -> int | None:
        """Row index for a work key ("/works/OL1W", "met/123", "mb/abc") or a
        title: exact title match first, then 'starts with'."""
        if not hasattr(self, "_key_index"):
            self._key_index = {k: i for i, k in enumerate(self.df["key"])}
        if title in self._key_index:
            return self._key_index[title]
        t = title.strip().lower()
        titles = self.df["title"].str.lower()
        for mask in (titles == t, titles.str.startswith(t)):
            hits = self.df.index[mask]
            if len(hits):
                # Prefer the most-published edition when titles repeat.
                return int(self.df.loc[hits, "edition_count"].idxmax())
        return None

    def search(self, query: str, n: int = 10) -> list[dict]:
        q = query.strip().lower()
        if not q:
            return []
        mask = self.df["title"].str.lower().str.contains(q, regex=False)
        hits = self.df[mask].sort_values("edition_count", ascending=False)
        out, seen = [], set()
        for i in hits.index:  # one entry per work, not per edition
            ident = self._identity(int(i))
            if ident in seen:
                continue
            seen.add(ident)
            out.append(self._card(int(i)))
            if len(out) == n:
                break
        return out

    def _scores(self, idx: int, method: str) -> np.ndarray:
        # Rows are normalised, so a dot product is the cosine similarity.
        tags = (self.matrix @ self.matrix[idx].T).toarray().ravel()
        if method == "tags" or self.embeddings is None:
            return tags
        meaning = self.embeddings @ self.embeddings[idx]
        if method == "meaning":
            return meaning
        return BLEND_TAGS * tags + (1 - BLEND_TAGS) * meaning

    def recommend(self, title: str, n: int = 5, across: str | None = None, method: str | None = None) -> list[dict] | None:
        """Closest works. across="collection" or "domain" keeps only works
        from a different collection, or a different kind of work entirely."""
        idx = self.find(title)
        if idx is None:
            return None
        return self._neighbors(idx, n, across, method)

    def _neighbors(self, idx: int, n: int = 5, across: str | None = None, method: str | None = None,
                   exclude: set | None = None) -> list[dict]:
        method = method or self.default_method
        if self.embeddings is None:
            method = "tags"
        scores = self._scores(idx, method)
        scores[idx] = -1  # never recommend the work itself
        if across in ("collection", "domain"):
            same = self.df[across] == self.df.at[idx, across]
            scores[same.to_numpy()] = -1
        order = np.argsort(-scores)
        out = []
        # Open Library keeps separate records for editions of one work, so
        # skip anything with the same title and author as the query or as a
        # result already chosen.
        seen = {self._identity(idx)} | (exclude or set())
        for j in order:
            if scores[j] < MIN_SCORE[method] or len(out) == n:
                break
            if self._identity(int(j)) in seen:
                continue
            seen.add(self._identity(int(j)))
            card = self._card(int(j))
            card["score"] = round(float(scores[j]), 3)
            card["shared_subjects"] = self._shared(idx, int(j))
            card["method"] = method
            out.append(card)
        return out

    def bridges(self, title: str, n: int = 5, across: str = "collection", method: str | None = None) -> list[dict] | None:
        """The closest works from other collections (or, with across="domain",
        from another art form: a book to a painting, a painting to a musician)."""
        return self.recommend(title, n=n, across=across, method=method)

    def graph(self, ref: str, n: int = 6, second: int = 2, method: str | None = None) -> dict | None:
        """A small constellation around one work, for the explorer:
        the center, its closest works in other art forms (bridges across
        domains), its closest kin in its own form, and a second ring of
        bridges from each first-ring work."""
        idx = self.find(ref)
        if idx is None:
            return None
        nodes = {self.df.at[idx, "key"]: {**self._card(idx), "ring": 0}}
        edges = []

        def add(src_key: str, cards: list[dict], ring: int, kind: str):
            for c in cards:
                if c["key"] not in nodes:
                    nodes[c["key"]] = {k: v for k, v in c.items() if k not in ("score", "shared_subjects", "method")} | {"ring": ring}
                edges.append({"source": src_key, "target": c["key"], "score": c["score"],
                              "shared": c["shared_subjects"], "kind": kind, "method": c["method"]})

        center = self.df.at[idx, "key"]
        seen = {self._identity(idx)}
        first = self._neighbors(idx, n, "domain", method)
        kin = self._neighbors(idx, max(2, n // 2), None, method)
        kin = [c for c in kin if c["domain"] == self.df.at[idx, "domain"]][: max(2, n // 2)]
        add(center, first, 1, "bridge")
        add(center, kin, 1, "kin")
        seen |= {(c["title"].strip().lower(), str(c["author"]).strip().lower()) for c in first + kin}
        for c in first:
            j = self.find(c["key"])
            more = self._neighbors(j, second, "domain", method, exclude=seen)
            add(c["key"], more, 2, "bridge")
        return {"center": center, "nodes": list(nodes.values()), "edges": edges,
                "method": (method or self.default_method) if self.embeddings is not None else "tags"}

    # ── helpers ───────────────────────────────────────────────────────
    def _identity(self, i: int) -> tuple[str, str]:
        row = self.df.iloc[i]
        return (row["title"].strip().lower(), str(row["author_name"]).strip().lower())

    def _shared(self, a: int, b: int, limit: int = 5) -> list[str]:
        sa = {s.lower(): s for s in self.df.at[a, "subjects"]}
        common = {s.lower(): sa[s.lower()] for s in self.df.at[b, "subjects"] if s.lower() in sa}
        return sorted(common.values(), key=str.lower)[:limit]

    def _card(self, i: int) -> dict:
        row = self.df.iloc[i]
        year = int(row["first_publish_year"]) if row["first_publish_year"] else None
        card = {
            "title": row["title"],
            # Artworks and musicians often have no author: pandas stores that
            # as NaN, which JSON can't carry, so send None instead.
            "author": row["author_name"] if isinstance(row["author_name"], str) and row["author_name"] else None,
            "year": year,
            "domain": row["domain"],
            "collection": row["collection"],
            "key": row["key"],
        }
        for extra in ("image", "url"):
            if extra in row and isinstance(row[extra], str) and row[extra]:
                card[extra] = row[extra]
        return card

    def card(self, title: str) -> dict | None:
        idx = self.find(title)
        return None if idx is None else self._card(idx)


def main():
    rec = Recommender.build()
    print(f"{len(rec.df)} works, {len(rec.vectorizer.vocabulary_)} subject tags")
    for query in ["Blues people", "Ways of Seeing", "Lady sings the blues"]:
        for label, fn in [("Similar", rec.recommend), ("Bridges", rec.bridges)]:
            results = fn(query)
            if results is None:
                print(f"\n'{query}' not found.")
                break
            print(f"\n{label} to '{query}':")
            for r in results:
                why = ", ".join(r["shared_subjects"])
                print(f"  {r['score']:.3f}  {r['title']} — {r['author']} [{r['collection']}]  ({why})")


if __name__ == "__main__":
    main()
