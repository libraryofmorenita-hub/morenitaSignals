"""
src/collect/met_museum.py

Stage 1 — Collect: The Metropolitan Museum of Art Open Access API
-----------------------------------------------------------------
The Met provides a free, no-auth API for 500k+ artworks.
Docs: https://metmuseum.github.io/

YOUR GOAL: Search for artworks by department or keyword, fetch their
metadata, and save to data/raw/met_museum_{query}.json

API endpoints:
  Search:  https://collectionapi.metmuseum.org/public/collection/v1/search?q=QUERY&hasImages=true
  Object:  https://collectionapi.metmuseum.org/public/collection/v1/objects/OBJECT_ID

The search endpoint returns {"total": N, "objectIDs": [...]}
You then fetch each objectID individually for full metadata.

IMPORTANT: The object endpoint can return a lot of IDs (tens of thousands).
Cap yourself at 200 objects per query — use objectIDs[:200].

QUERIES TO START WITH:
  "latin america", "africa", "india", "textiles", "ceramics",
  "impressionism", "folk art"

EACH OBJECT has fields like:
  objectID, title, artistDisplayName, department, objectDate,
  primaryImageSmall, country, culture, medium, classification

HINTS:
  - The search endpoint gives you IDs only — loop to fetch each object
  - Sleep 0.1s between object fetches (more lenient API, but still be polite)
  - Wrap individual object fetches in try/except — some IDs return 404
  - Save a list of dicts, one per artwork

START HERE — write your imports first, then fill in the functions:
"""

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

SEARCH_URL = "https://collectionapi.metmuseum.org/public/collection/v1/search"
OBJECT_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects/{}"


def search_object_ids(query: str, limit: int = 200) -> list[int]:
    """
    Search for object IDs matching a query.

    Returns
    -------
    list[int]  up to `limit` object IDs

    TODO: GET SEARCH_URL with params q=query, hasImages=true
          return response["objectIDs"][:limit] — handle None if no results
    """
    pass


def fetch_object(object_id: int) -> dict | None:
    """
    Fetch full metadata for one artwork by ID.

    Returns
    -------
    dict  the artwork metadata, or None if fetch fails

    TODO: GET OBJECT_URL.format(object_id)
          return .json() — wrap in try/except for failed requests
    """
    pass


def collect_query(query: str) -> list[dict]:
    """
    Fetch all objects for a query and return as a list.

    TODO:
      - Call search_object_ids()
      - Loop over IDs, call fetch_object() for each
      - Collect non-None results
      - Sleep 0.1s between fetches
      - Print progress every 25 objects
    """
    pass


def save_raw(query: str, artworks: list[dict]) -> Path:
    """Save to data/raw/met_museum_{query}.json — similar to open_library.py"""
    pass


def main():
    pass


if __name__ == "__main__":
    main()
