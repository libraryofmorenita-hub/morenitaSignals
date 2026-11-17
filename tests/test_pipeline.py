"""Pipeline mappers and cross-domain bridges, on hand-made records (no network)."""

import pandas as pd

from src.clean.pipeline import _year, from_met, from_musicbrainz, from_open_library, normalize
from src.model.recommender import Recommender

MET = {
    "objectID": 316456, "title": "Kente Cloth", "artistDisplayName": "",
    "objectBeginDate": 1900, "culture": "Asante", "country": "Ghana",
    "classification": "Textiles-Woven", "objectName": "Cloth", "department": "The Michael C. Rockefeller Wing",
    "tags": [{"term": "Africa"}, {"term": "Textiles"}],
    "primaryImageSmall": "https://images.metmuseum.org/x.jpg", "objectURL": "https://www.metmuseum.org/art/collection/search/316456",
}
MB = {"id": "abc", "name": "Fela Kuti", "begin": "1938-10-15", "area": "Nigeria", "begin_area": "Abeokuta", "tags": ["afrobeat", "Africa", "jazz"]}
OL = {"key": "/works/OL1W", "title": "Things Fall Apart", "author_name": ["Chinua Achebe"], "subject": ["Africa", "Nigeria", "Igbo"], "first_publish_year": 1958}


def test_year_parsing():
    assert _year("1938-10-15") == 1938
    assert _year("ca. 1890") == 1890
    assert _year(None) == 0


def test_mappers_share_one_schema():
    rows = [from_open_library(OL), from_met(MET), from_musicbrainz(MB)]
    assert {r["domain"] for r in rows} == {"book", "art", "music"}
    art = rows[1]
    assert art["key"] == "met/316456" and art["author_name"] is None
    assert {"Africa", "Ghana", "Asante"} <= set(art["subject"])
    assert rows[2]["first_publish_year"] == 1938 and "Nigeria" in rows[2]["subject"]


def test_cross_domain_bridges():
    rows = []
    for row, coll in [(from_open_library(OL), "african literature"), (from_met(MET), "africa"), (from_musicbrainz(MB), "afrobeat")]:
        row["collection"] = coll
        rows.append(row)
    # a second book so tags appear at least twice (TF-IDF min_df=2)
    extra = from_open_library({"key": "/works/OL2W", "title": "Half of a Yellow Sun", "author_name": ["Chimamanda Ngozi Adichie"], "subject": ["Nigeria", "Igbo", "Africa"]})
    extra["collection"] = "african literature"
    rows.append(extra)
    rec = Recommender.build(normalize(pd.DataFrame(rows)))
    bridges = rec.bridges("Things Fall Apart", across="domain")
    assert bridges and all(b["domain"] != "book" for b in bridges)
    assert bridges[0]["title"] == "Fela Kuti"  # shares Africa and Nigeria
