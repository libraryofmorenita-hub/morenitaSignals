"""The live explorer (docs/static-api.js) must draw the same constellations
as the API. Builds the static files for the test dataset, runs static-api.js
in Node and compares every graph with Recommender.graph. Skips without Node."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.model.recommender import Recommender
from tools.build_static import build

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


def _shape(graph: dict) -> tuple:
    nodes = sorted((n["key"], n["ring"]) for n in graph["nodes"])
    edges = sorted((e["source"], e["target"], e["kind"], round(float(e["score"]), 3), tuple(e["shared"])) for e in graph["edges"])
    return graph["center"], nodes, edges, graph["method"]


@pytest.fixture
def rec():
    """60 works in three art forms with overlapping tags and random meaning
    vectors: enough links to fill both rings and exercise every method."""
    rng = np.random.default_rng(7)
    tags = [f"theme {i}" for i in range(14)]
    domains = ["book", "art", "music"]
    rows = []
    for i in range(60):
        d = domains[i % 3]
        rows.append({
            "title": f"Work {i}" if i % 17 else "Work 1",  # a repeated title, like book editions
            "author_name": f"Maker {i % 23}",
            "subject": list(rng.choice(tags, size=4, replace=False)),
            "collection": f"{d} {i % 2}",
            "domain": d,
            "first_publish_year": 1900 + i,
            "edition_count": int(rng.integers(1, 30)),
            "key": f"/w/{i}",
        })
    emb = rng.normal(size=(60, 16))
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)
    return Recommender.build(pd.DataFrame(rows), embeddings=emb)


@pytest.mark.skipif(NODE is None, reason="Node is not installed")
@pytest.mark.parametrize("method", ["tags", "meaning", "blend"])
def test_static_graph_matches_api(rec, tmp_path, method):
    build(rec, tmp_path)
    keys = rec.df["key"].tolist()
    out = subprocess.run(
        [NODE, str(ROOT / "tests" / "static_harness.js"), str(ROOT / "docs" / "static-api.js"), str(tmp_path), method, *keys],
        capture_output=True, text=True, check=True,
    )
    static = json.loads(out.stdout)
    for k in keys:
        assert _shape(static[k]) == _shape(rec.graph(k, method=method)), k
    assert sum(len(g["edges"]) for g in static.values()) > 300  # the rings are full, not trivially empty
