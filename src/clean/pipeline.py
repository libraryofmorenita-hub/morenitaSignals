"""
src/clean/pipeline.py

Stage 2 — Clean: one table for books, artworks and music
---------------------------------------------------------
Reads every raw file in data/raw/ and maps each source onto the same schema:

    key, title, author_name, subject (list of tags), first_publish_year,
    language, edition_count, domain, collection, collections

  domain      what kind of work: "book", "art" or "music"
  collection  the search it came from ("jazz", "africa", "flamenco"...)

The file name says the source and the collection:
    open_library_jazz.json   -> book,  "jazz"
    met_museum_africa.json   -> art,   "africa"
    musicbrainz_flamenco.json-> music, "flamenco"
"""


from __future__ import annotations
import json
import re
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
CLEAN_DIR = Path(__file__).resolve().parents[2] / "data" / "clean"


def _year(value) -> int:
    """First 4-digit year in a value like '1957-03-02' or 'ca. 1890', else 0."""
    if isinstance(value, (int, float)) and value == value:
        return int(value)
    m = re.search(r"-?\d{3,4}", str(value or ""))
    return int(m.group()) if m else 0


def _first(value):
    return value[0] if isinstance(value, list) and value else None


# ── one mapper per source ────────────────────────────────────────────
def from_open_library(doc: dict) -> dict:
    return {
        "key": doc.get("key", ""),
        "title": doc.get("title", ""),
        "author_name": _first(doc.get("author_name")),
        "subject": doc.get("subject") or [],
        "first_publish_year": _year(doc.get("first_publish_year")),
        "language": _first(doc.get("language")),
        "edition_count": doc.get("edition_count") or 0,
        "domain": "book",
    }


def from_met(obj: dict) -> dict:
    # An artwork's "subjects" are its keyword tags plus what it is and where
    # it's from, which is what lets a Yoruba textile meet an African novel.
    tags = [t.get("term") for t in obj.get("tags") or [] if t.get("term")]
    tags += [obj.get(k) for k in ("culture", "country", "classification", "objectName", "department") if obj.get(k)]
    return {
        "key": f"met/{obj.get('objectID')}",
        "title": obj.get("title") or "",
        "author_name": obj.get("artistDisplayName") or None,
        "subject": tags,
        "first_publish_year": _year(obj.get("objectBeginDate") or obj.get("objectDate")),
        "language": None,
        "edition_count": 0,
        "domain": "art",
        "image": obj.get("primaryImageSmall") or None,
        "url": obj.get("objectURL") or None,
    }


def from_musicbrainz(artist: dict) -> dict:
    tags = list(artist.get("tags") or [])
    tags += [p for p in (artist.get("area"), artist.get("begin_area")) if p]
    return {
        "key": f"mb/{artist.get('id')}",
        "title": artist.get("name") or "",
        "author_name": artist.get("name") or None,
        "subject": tags,
        "first_publish_year": _year(artist.get("begin")),
        "language": None,
        "edition_count": 0,
        "domain": "music",
    }


SOURCES = {
    "open_library_": from_open_library,
    "met_museum_": from_met,
    "musicbrainz_": from_musicbrainz,
}


def load_raw() -> list[dict]:
    rows = []
    for file in sorted(RAW_DIR.glob("*.json")):
        prefix = next((p for p in SOURCES if file.stem.startswith(p)), None)
        if prefix is None:
            print(f"Skipping {file.name}: unknown source")
            continue
        collection = file.stem.removeprefix(prefix).replace("_", " ")
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            row = SOURCES[prefix](item)
            row["collection"] = collection
            rows.append(row)
    return rows


def make_dataframe(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df["title"] = df["title"].fillna("").astype(str).str.strip()
    df["key"] = df["key"].fillna("")
    df["first_publish_year"] = df["first_publish_year"].fillna(0).astype(int)
    df["edition_count"] = df["edition_count"].fillna(0).astype(int)
    df = df[df["title"] != ""]
    # The same work can show up under two searches (a jazz book that is also
    # African literature). Keep one row per work and remember every
    # collection it belongs to.
    collections = df.groupby("key")["collection"].apply(lambda s: sorted(set(s)))
    df = df.drop_duplicates(subset="key").copy()
    df["collections"] = df["key"].map(collections)
    df["collection"] = df["collections"].str[0]
    return df.reset_index(drop=True)


def save_clean(df: pd.DataFrame) -> Path:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    filepath = CLEAN_DIR / "clean.parquet"
    df.to_parquet(filepath, index=False)
    print(f"Saved {len(df)} records to {filepath}")
    print(df["domain"].value_counts().to_string())
    return filepath


def main():
    df = normalize(make_dataframe(load_raw()))
    save_clean(df)


if __name__ == "__main__":
    main()
