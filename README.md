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

# Stage 4: train model
python -m src.model.embeddings
python -m src.model.recommender

# Stage 5: run API
uvicorn api.main:app --reload
```

## Status

- [ ] Stage 1 — Data collection
- [ ] Stage 2 — Pipeline + cleaning
- [ ] Stage 3 — EDA + NLP
- [ ] Stage 4 — Embedding model + recommender
- [ ] Stage 5 — API + dashboard

---

Built by [Amelia Arabe](https://www.linkedin.com/in/ameliaarabe) · Morenita Collective
