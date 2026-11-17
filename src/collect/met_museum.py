"""
src/collect/met_museum.py

Stage 1 — Collect: The Metropolitan Museum of Art Open Access API
-----------------------------------------------------------------
The Met provides a free, no-auth API for 500k+ artworks.
Docs: https://metmuseum.github.io/

Searches the Met for each query, fetches every artwork's metadata, and saves
data/raw/met_museum_{query}.json (one list of artwork dicts per query).

Run:  python -m src.collect.met_museum
      python -m src.collect.met_museum --limit 20     (quick test)
"""


from __future__ import annotations
import argparse
import json
import time
from pathlib import Path

import requests

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

QUERIES = [
    "latin america",
    "africa",
    "india",
    "textiles",
    "folk art",
    "impressionism",
]

# v1 search was retired on 1 Oct 2026 (it now returns 410 Gone); v1.1 replaces it.
SEARCH_URL = "https://collectionapi.metmuseum.org/public/collection/v1.1/search"
OBJECT_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects/{}"
HEADERS = {"User-Agent": "MorenitaSignals/0.1 (https://github.com/libraryofmorenita-hub/morenitaSignals)"}

# Only the fields the pipeline uses, so raw files stay small.
KEEP = [
    "objectID", "title", "artistDisplayName", "department", "objectDate",
    "objectBeginDate", "culture", "country", "medium", "classification",
    "objectName", "tags", "primaryImageSmall", "objectURL", "isPublicDomain",
]


# The Met's servers block clients that ask too fast (403 Forbidden), so go
# slowly, and when blocked, wait and try again instead of giving up.
DELAY = 0.6          # seconds between requests
BACKOFF = [10, 30, 60]  # waits after a 403/429 before retrying


def _get(url: str, params: dict | None = None) -> requests.Response | None:
    for wait in [0] + BACKOFF:
        if wait:
            print(f"    blocked, waiting {wait}s...")
            time.sleep(wait)
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=30)
        except requests.RequestException:
            continue
        if r.status_code in (403, 429, 503):
            continue
        return r
    return None


def search_object_ids(query: str, limit: int = 200) -> list[int]:
    """Up to `limit` object IDs for a query (artworks with images only)."""
    r = _get(SEARCH_URL, {"q": query, "hasImages": "true", "limit": min(limit, 500)})
    if r is None or r.status_code != 200:
        print(f"'{query}': search failed, skipping for now")
        return []
    ids = r.json().get("objectIDs") or []  # the API returns null when nothing matches
    return ids[:limit]


def fetch_object(object_id: int) -> dict | None:
    """Full metadata for one artwork, trimmed to KEEP, or None if it fails."""
    r = _get(OBJECT_URL.format(object_id))
    if r is None or r.status_code != 200:
        return None
    try:
        data = r.json()
    except ValueError:
        return None
    return {k: data.get(k) for k in KEEP}


def collect_query(query: str, limit: int = 200) -> list[dict]:
    ids = search_object_ids(query, limit)
    print(f"'{query}': {len(ids)} objects to fetch")
    artworks = []
    for n, object_id in enumerate(ids, 1):
        art = fetch_object(object_id)
        if art and art.get("title"):
            artworks.append(art)
        if n % 25 == 0:
            print(f"  {n}/{len(ids)} fetched, {len(artworks)} kept")
        time.sleep(DELAY)
    return artworks


def save_raw(query: str, artworks: list[dict]) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"met_museum_{query.replace(' ', '_')}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(artworks, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(artworks)} artworks to {path.name}")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=200, help="objects per query")
    parser.add_argument("--redo", action="store_true", help="re-collect queries already saved")
    args = parser.parse_args()
    for query in QUERIES:
        path = RAW_DIR / f"met_museum_{query.replace(' ', '_')}.json"
        if path.exists() and not args.redo:
            print(f"'{query}': already saved, skipping (use --redo to fetch again)")
            continue
        artworks = collect_query(query, args.limit)
        if artworks:  # don't save an empty file over a blocked run
            save_raw(query, artworks)


if __name__ == "__main__":
    main()
