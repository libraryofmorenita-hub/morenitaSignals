"""
src/collect/open_library.py

Stage 1 — Collect: Open Library API
------------------------------------
Open Library offers a free, no-auth-required API for books and authors.
Docs: https://openlibrary.org/developers/api

YOUR GOAL: Write a script that searches for books by subject,
fetches their metadata, and saves raw JSON to data/raw/.

API endpoints you'll use:
  Search:  https://openlibrary.org/search.json?subject=SUBJECT&limit=100&page=N
  Work:    https://openlibrary.org/works/OL123W.json  (detail for one book)

The search endpoint returns a list of 'docs'. Each doc has fields like:
  - key, title, author_name, subject, first_publish_year, language, edition_count

SUBJECTS TO COLLECT (start with these, add more as you go):
  "latin american literature", "african literature", "south asian fiction",
  "indigenous peoples", "jazz", "classical music", "visual arts"

HOW TO THINK ABOUT THIS FILE:
  1. One function to fetch a single page from the search API
  2. One function to paginate through all results for a subject
  3. One function to save results to data/raw/open_library_{subject}.json
  4. A main() block that loops over all subjects and collects them

HINTS:
  - requests.get(url).json() returns a Python dict from JSON
  - Use time.sleep(1) between requests — be polite to free APIs
  - Print progress so you know it's working: print(f"Fetched page {n}...")
  - Check the 'numFound' key in the response to know the total count
  - Store the raw response as-is — don't transform yet (that's Stage 2)

START HERE — write your imports first:
"""

import json
import time
from pathlib import Path

import requests

# Path to save raw data — Path makes cross-platform file handling easy
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

# Subjects you want to collect
SUBJECTS = [
    "latin american literature",
    "african literature",
    "south asian fiction",
    "indigenous peoples",
    "jazz",
    "classical music",
    "visual arts",
]

BASE_URL = "https://openlibrary.org/search.json"


# ── YOUR CODE STARTS HERE ──────────────────────────────────────────────────


def fetch_page(subject: str, page: int, limit: int = 100) -> dict:
    """
    Fetch one page of search results for a subject from Open Library.

    Parameters
    ----------
    subject : str   e.g. "latin american literature"
    page    : int   1-indexed page number
    limit   : int   results per page (max 100)

    Returns
    -------
    dict    the raw JSON response from the API

    TODO: build the params dict, call requests.get(), return .json()
    Hint: params = {"subject": subject, "limit": limit, "page": page, "fields": "key,title,author_name,subject,first_publish_year,language,edition_count"}
    """
    pass


def collect_subject(subject: str, max_pages: int = 5) -> list[dict]:
    """
    Paginate through results for a subject and return all docs.

    Parameters
    ----------
    subject   : str  the subject to search
    max_pages : int  safety cap so you don't accidentally fetch thousands

    Returns
    -------
    list[dict]  all doc entries collected across pages

    TODO:
      - Call fetch_page() in a loop
      - Accumulate docs from response["docs"] into a list
      - Stop early if a page comes back empty (no more results)
      - Sleep 1 second between pages
      - Print progress
    """
    pass


def save_raw(subject: str, docs: list[dict]) -> Path:
    """
    Save collected docs to data/raw/open_library_{subject}.json

    Parameters
    ----------
    subject : str         the subject name (used in filename)
    docs    : list[dict]  the docs to save

    Returns
    -------
    Path  the file path where data was saved

    TODO:
      - Sanitize the subject name for a filename (replace spaces with underscores)
      - Use json.dump() to write the list to a .json file
      - Print how many records were saved and where
    """
    pass


def main():
    """
    Loop over all SUBJECTS, collect data, and save to disk.

    TODO: call collect_subject() and save_raw() for each subject
    """
    pass


if __name__ == "__main__":
    main()
