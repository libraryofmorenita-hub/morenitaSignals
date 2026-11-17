"""
src/collect/musicbrainz.py

Stage 1 — Collect: MusicBrainz API
------------------------------------
MusicBrainz is a free, open music encyclopedia. No auth for basic search,
but it requires a User-Agent and allows about one request per second.
Docs: https://musicbrainz.org/doc/MusicBrainz_API

Searches artists by genre tag and saves data/raw/musicbrainz_{genre}.json.

Run:  python -m src.collect.musicbrainz
      python -m src.collect.musicbrainz --max 100     (quick test)
"""


from __future__ import annotations
import argparse
import json
import time
from pathlib import Path

import requests

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

GENRES = [
    "jazz", "bossa nova", "cumbia", "afrobeat", "flamenco",
    "classical", "son jarocho", "blues",
]

URL = "https://musicbrainz.org/ws/2/artist/"
HEADERS = {"User-Agent": "MorenitaSignals/0.1 (https://github.com/libraryofmorenita-hub/morenitaSignals)"}
PAGE = 100


def fetch_page(genre: str, offset: int) -> dict:
    params = {"query": f'tag:"{genre}"', "fmt": "json", "limit": PAGE, "offset": offset}
    for attempt in range(3):
        r = requests.get(URL, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 503:  # rate limited: back off and retry
            time.sleep(3 * (attempt + 1))
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()
    return {}


def slim(artist: dict) -> dict:
    """Keep only what the pipeline uses."""
    area = artist.get("area") or {}
    begin_area = artist.get("begin-area") or {}
    return {
        "id": artist.get("id"),
        "name": artist.get("name"),
        "type": artist.get("type"),
        "country": artist.get("country"),
        "area": area.get("name"),
        "begin_area": begin_area.get("name"),
        "begin": (artist.get("life-span") or {}).get("begin"),
        "tags": [t["name"] for t in artist.get("tags", []) if t.get("count", 0) >= 1],
        "score": artist.get("score"),
    }


def collect_genre(genre: str, max_results: int = 500) -> list[dict]:
    artists, offset = [], 0
    while offset < max_results:
        data = fetch_page(genre, offset)
        batch = data.get("artists", [])
        if not batch:
            break
        artists.extend(slim(a) for a in batch)
        total = min(data.get("count", 0), max_results)
        print(f"'{genre}': {len(artists)}/{total}")
        offset += PAGE
        if offset >= total:
            break
        time.sleep(1.5)  # MusicBrainz is strict about one request a second
    return artists


def save_raw(genre: str, artists: list[dict]) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"musicbrainz_{genre.replace(' ', '_')}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(artists, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(artists)} artists to {path.name}")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=500, help="artists per genre")
    args = parser.parse_args()
    for genre in GENRES:
        save_raw(genre, collect_genre(genre, args.max))
        time.sleep(1.5)


if __name__ == "__main__":
    main()
