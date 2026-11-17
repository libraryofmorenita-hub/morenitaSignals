"""API tests against the real cleaned data. Skipped if the data isn't built yet
(run Stage 1 and Stage 2 first)."""

from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "data" / "clean" / "clean.parquet"
pytestmark = pytest.mark.skipif(not DATA.exists(), reason="run the pipeline first")


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app

    with TestClient(app) as c:
        yield c


def test_root(client):
    body = client.get("/").json()
    assert body["works"] > 0 and "jazz" in body["collections"]


def test_recommend_and_bridges(client):
    r = client.get("/recommend/Blues people")
    assert r.status_code == 200 and r.json()["recommendations"]
    b = client.get("/bridges/Blues people").json()
    assert all(x["collection"] != b["query"]["collection"] for x in b["bridges"])


def test_not_found_is_404(client):
    assert client.get("/recommend/zzzz not a book").status_code == 404


def test_search(client):
    assert client.get("/search", params={"q": "jazz"}).json()["results"]


def test_graph_and_explorer(client):
    g = client.get("/graph", params={"ref": "Things fall apart"}).json()
    assert g["center"] and g["nodes"][0]["ring"] == 0
    keys = {n["key"] for n in g["nodes"]}
    assert all(e["source"] in keys and e["target"] in keys for e in g["edges"])
    assert client.get("/graph", params={"ref": "zzzz not a book"}).status_code == 404
    assert "Signals" in client.get("/explore").text


def test_graph_is_cached(client):
    a = client.get("/graph", params={"ref": "Blues people"}).json()
    b = client.get("/graph", params={"ref": "blues people "}).json()
    assert a == b
