# Morenita Signals

A cultural intelligence ML pipeline that maps relationships between creative works — literature, visual art, and music — across cultures and time periods.

Built to power personalized learning journeys on [Library of Morenita](https://libraryofmorenita-hub.github.io/muses-of-morenita).

---

## What it does

1. **Collect** — ingests data from Open Library, Met Museum, and MusicBrainz open APIs
2. **Clean** — normalizes and structures raw data into a unified schema
3. **Analyze** — exploratory analysis + NLP theme extraction across cultural domains
4. **Model** — trains a recommendation engine using text embeddings and clustering
5. **Ship** — serves recommendations via FastAPI, visualized in an interactive dashboard

## Tech stack

- Python 3.11+
- pandas, NumPy — data wrangling
- spaCy — NLP / keyword extraction
- scikit-learn — clustering, nearest neighbors
- sentence-transformers — text embeddings
- FastAPI — recommendation API
- Plotly / Streamlit — visualization dashboard

## Project structure

```
morenita-signals/
├── data/
│   ├── raw/        # raw JSON from APIs (git-ignored)
│   └── clean/      # processed Parquet files (git-ignored)
├── notebooks/      # EDA and exploration
├── src/
│   ├── collect/    # API ingestion scripts
│   ├── clean/      # data pipeline + normalization
│   ├── analyze/    # EDA helpers + NLP
│   └── model/      # embeddings + recommender
├── api/            # FastAPI app
└── tests/
```

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/morenita-signals.git
cd morenita-signals
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the pipeline

```bash
# Stage 1: collect raw data
python -m src.collect.open_library
python -m src.collect.met_museum
python -m src.collect.musicbrainz

# Stage 2: clean + normalize
python -m src.clean.pipeline

# Stage 3: explore (Jupyter)
jupyter notebook notebooks/

# Stage 4: try the recommender
python -m src.model.recommender

# Stage 5: run API
uvicorn api.main:app --reload
```

## Status

- [x] Stage 1 — Data collection *(Open Library: 7 collections, 3,130 works. Met Museum and MusicBrainz collectors written; run them to add art and music)*
- [x] Stage 2 — Pipeline + cleaning *(books, artworks and musicians in one table, each tagged with its domain and collection)*
- [x] Stage 3 — EDA *(NLP/keyword extraction not started)*
- [x] Stage 4 — Recommender *(TF-IDF + cosine similarity with cross-collection bridges and explanations, not yet the embeddings/clustering originally planned)*
- [x] Stage 5 — API *(`/search`, `/recommend`, `/bridges`, `/graph`, with tests)* and the explorer at `/explore`
- [ ] Next — run the Met and MusicBrainz collectors, sentence-transformer embeddings, dashboard

## How it recommends

Each work is described by its subject tags. Tags that describe a book's form
rather than its ideas ("Fiction", "Biography", "History and criticism",
bookseller codes) are dropped, then TF-IDF weighs the rest so rare, specific
tags count more than common ones. Cosine similarity ranks the matches.

- **Recommend** returns the closest works overall.
- **Bridges** returns the closest works from a *different* collection, the
  links across cultures and art forms that Signals exists to find.
  `?across=domain` goes further: from a book only to artworks and musicians.
- Every result lists the subjects the two works share, so you can see why it matched.

```
$ curl "localhost:8000/bridges/Blues people?n=3"
Lift Ev'ry Voice and Sing (James Weldon Johnson)  [african literature]  0.297
  shared: African American music, African Americans, Music
Little known black history facts (Tom Joyner)      [african literature]  0.225
Great Negroes, past and Present (Russell L. Adams) [african literature]  0.212
```

Run the tests with `python -m pytest`.

## Explorer

`uvicorn api.main:app --reload`, then open http://127.0.0.1:8000/explore.
Search any book, artwork or musician and it becomes the center of a small
constellation: its bridges to other art forms, its closest kin, and a second
ring of bridges from each of those. Hover a line to see what two works share;
click any work to make it the center. The Meaning and Blend buttons switch on
once you've run `python -m src.model.embeddings`.

Every view has its own link (the ⧉ button copies it), the browser's back
button walks back along your trail, and the *i* button explains how links are
found. It works on a phone too.

## Scorecard

```bash
python -m src.eval.evaluate --verbose
```

Scores each matching method three ways: **probes** (hand-written checks in
`src/eval/probes.json`, e.g. *Blues people* should bridge to blues or jazz
musicians), **coverage** (share of works with at least one bridge strong
enough to show) and **diversity** (share of bridges that cross into another
collection).

| Method | Probes | Coverage | Diversity |
|---|---|---|---|
| Shared tags | 8/14 | 58% | 84% |
| Meaning | 12/14 | 100% | 89% |
| Blend | 13/14 | 100% | 89% |

Blend is the default for a reason. The one probe it still misses is Paco de
Lucía: the collection has no flamenco books or art yet. Add a probe whenever
you spot a link that should or shouldn't exist.

---

Built by [Amelia Arabe](https://www.linkedin.com/in/ameliaarabe) · Morenita Collective
