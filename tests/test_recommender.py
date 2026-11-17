"""Tests for the recommender, on a tiny hand-made dataset so they run anywhere."""

import pandas as pd
import pytest

from src.model.recommender import Recommender, _subjects


@pytest.fixture
def rec():
    df = pd.DataFrame(
        {
            "title": ["Blues People", "Stomping the Blues", "Lift Every Voice", "Ways of Seeing", "Blues People"],
            "author_name": ["Amiri Baraka", "Albert Murray", "James Weldon Johnson", "John Berger", "Amiri Baraka"],
            "subject": [
                ["Jazz", "Blues", "African Americans", "Music", "Fiction"],
                ["Jazz", "Blues", "Music"],
                ["African Americans", "Music", "Poetry"],
                ["Art", "Visual perception"],
                ["Jazz", "Blues", "African Americans"],
            ],
            "collection": ["jazz", "jazz", "african literature", "visual arts", "jazz"],
            "first_publish_year": [1963, 1976, 1900, 1972, 1999],
            "edition_count": [20, 5, 3, 17, 1],
            "key": ["/w/1", "/w/2", "/w/3", "/w/4", "/w/5"],
        }
    )
    return Recommender.build(df)


def test_generic_tags_are_dropped():
    assert _subjects(["Fiction", "Jazz", "MUSIC / Classical"]) == ["Jazz"]


def test_find_prefers_exact_then_prefix_and_most_editions(rec):
    assert rec.find("blues people") == 0  # 20 editions beats 1
    assert rec.find("stomping") == 1
    assert rec.find("nothing like this") is None


def test_recommend_skips_itself_and_duplicate_editions(rec):
    titles = [r["title"] for r in rec.recommend("Blues People")]
    assert "Blues People" not in titles
    assert titles[0] == "Stomping the Blues"


def test_results_explain_themselves(rec):
    top = rec.recommend("Blues People")[0]
    assert {"Blues", "Jazz"} <= set(top["shared_subjects"])
    assert 0 < top["score"] <= 1


def test_bridges_only_cross_collections(rec):
    bridges = rec.bridges("Blues People")
    assert bridges, "expected a cross-collection link"
    assert all(b["collection"] != "jazz" for b in bridges)
    assert bridges[0]["title"] == "Lift Every Voice"


def test_unrelated_work_has_no_weak_links(rec):
    assert rec.bridges("Ways of Seeing") == []


def test_search(rec):
    assert [r["title"] for r in rec.search("blues")][:1] == ["Blues People"]
    assert rec.search("  ") == []


def test_meaning_links_works_without_shared_tags(rec):
    import numpy as np

    # Fake "meaning" vectors: Ways of Seeing sits near Lift Every Voice even
    # though they share no tags, which tags alone can never find.
    emb = np.array([[1, 0, 0], [0.9, 0.1, 0], [0, 0.6, 0.8], [0, 0.6, 0.8], [1, 0, 0]], dtype=float)
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)
    rec2 = type(rec).build(rec.df.drop(columns=["subjects"]), embeddings=emb)
    assert rec2.default_method == "blend"
    assert rec.bridges("Ways of Seeing") == []  # tags only: nothing
    hits = rec2.bridges("Ways of Seeing", method="meaning")
    assert hits and hits[0]["title"] == "Lift Every Voice" and hits[0]["method"] == "meaning"
