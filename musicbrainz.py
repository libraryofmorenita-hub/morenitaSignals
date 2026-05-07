"""
src/collect/musicbrainz.py

Stage 1 — Collect: MusicBrainz API
------------------------------------
MusicBrainz is a free, open music encyclopedia with metadata on artists,
releases, and recordings. No auth needed for basic search.
Docs: https://musicbrainz.org/doc/MusicBrainz_API

YOUR GOAL: Search for artists by genre/tag, fetch their metadata,
and save to data/raw/musicbrainz_{genre}.json

API endpoint:
  https://musicbrainz.org/ws/2/artist/?query=tag:GENRE&fmt=json&limit=100&offset=N

REQUIRED HEADER — MusicBrainz requires a User-Agent or it will block you:
  headers = {"User-Agent": "MorenitaSignals/0.1 (your@email.com)"}

RESPONSE STRUCTURE:
  response["artists"] — list of artist dicts
  Each artist has: id, name, country, area, tags, begin-area, life-span

GENRES TO COLLECT:
  "jazz", "bossa nova", "cumbia", "afrobeat", "flamenco",
  "classical", "son jarocho", "blues"

HINTS:
  - Pagination uses 'offset' not 'page': offset=0, 100, 200...
  - Check response["count"] for total results (cap at 500 per genre)
  - Sleep 1.5s between requests — MusicBrainz is strict about rate limits
  - Some artist fields may be missing — use .get() to access them safely

START HERE:
"""

import json
import time
from pathlib import Path

import requests

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

# TODO: update the email to yours
HEADERS = {"User-Agent": "MorenitaSignals/0.1 (missameliava@gmail.com)"}

BASE_URL = "https://musicbrainz.org/ws/2/artist/"

GENRES = [
    "jazz",
    "bossa nova",
    "cumbia",
    "afrobeat",
    "flamenco",
    "classical",
    "blues",
]


def fetch_artists_page(genre: str, offset: int = 0, limit: int = 100) -> dict:
    """
    Fetch one page of artists for a genre tag.

    TODO: build params with query=f"tag:{genre}", fmt="json", limit, offset
          pass HEADERS in the request
          return .json()
    """
    pass


def collect_genre(genre: str, max_artists: int = 500) -> list[dict]:
    """
    Paginate through all artists for a genre.

    TODO: loop with offset=0, 100, 200...
          stop when artists list is empty or total reached
          sleep 1.5s between pages
    """
    pass


def save_raw(genre: str, artists: list[dict]) -> Path:
    """Save to data/raw/musicbrainz_{genre}.json"""
    pass


def main():
    pass


if __name__ == "__main__":
    main()
