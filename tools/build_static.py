"""
tools/build_static.py

Builds a static copy of the Signals explorer in docs/ so it runs on GitHub
Pages with no server. The recommender runs once here, ahead of time: every
work's nearest neighbors are saved for each method, and docs/static-api.js
answers the explorer's requests (/, /search, /graph) in the browser from
those files, following the same rules as api/main.py and Recommender.graph.

Run from the project root, after the data and embeddings exist:
    python tools/build_static.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.model.recommender import MIN_SCORE, Recommender  # noqa: E402

DOCS = ROOT / "docs"
BRIDGES = 10  # cross-domain candidates per work (the graph uses 6, plus room for exclusions)
NEAR = 3      # nearest works of any domain (the graph keeps those in the same domain)


def neighbor_rows(rec: Recommender, idx: int, method: str, across: str | None, n: int) -> list:
    """Top-n neighbors as [index, score], with the same filters as Recommender._neighbors."""
    scores = rec._scores(idx, method)
    scores[idx] = -1
    if across:
        same = rec.df[across] == rec.df.at[idx, across]
        scores[same.to_numpy()] = -1
    out, seen = [], {rec._identity(idx)}
    for j in np.argsort(-scores):
        if scores[j] < MIN_SCORE[method] or len(out) == n:
            break
        ident = rec._identity(int(j))
        if ident in seen:
            continue
        seen.add(ident)
        out.append([int(j), round(float(scores[j]), 3)])
    return out


def build(rec: Recommender, docs: Path = DOCS) -> None:
    """Write the static site for this recommender into docs (the tests use a temp folder)."""
    data = docs / "data"
    data.mkdir(parents=True, exist_ok=True)
    df = rec.df
    methods = ["tags"] if rec.embeddings is None else ["tags", "meaning", "blend"]

    works = []
    for i in range(len(df)):
        card = rec._card(i)
        card["subjects"] = [str(s) for s in df.at[i, "subjects"]]
        card["editions"] = int(df.at[i, "edition_count"] or 0)
        works.append(card)
    (data / "works.json").write_text(json.dumps(works, separators=(",", ":"), ensure_ascii=False))

    for m in methods:
        rows = []
        for i in range(len(df)):
            rows.append([neighbor_rows(rec, i, m, "domain", BRIDGES), neighbor_rows(rec, i, m, None, NEAR)])
        (data / f"neighbors-{m}.json").write_text(json.dumps(rows, separators=(",", ":")))

    info = {
        "message": "Morenita Signals (static build)",
        "works": int(len(df)),
        "collections": sorted(df["collection"].unique().tolist()),
        "domains": {k: int(v) for k, v in df["domain"].value_counts().to_dict().items()},
        "method": rec.default_method,
        "methods": methods,
    }
    (data / "info.json").write_text(json.dumps(info, separators=(",", ":")))

    page = (ROOT / "web" / "explore.html").read_text()
    page = page.replace("</head>", '<script src="static-api.js"></script>\n</head>', 1)
    (docs / "index.html").write_text(page)
    (docs / ".nojekyll").write_text("")
    size = sum(p.stat().st_size for p in data.iterdir())
    print(f"{docs.name}/ written: {len(df)} works, {size / 1e6:.1f} MB of data")


def main() -> None:
    build(Recommender.build())


if __name__ == "__main__":
    main()
