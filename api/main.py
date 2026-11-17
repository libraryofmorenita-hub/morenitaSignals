"""
Stage 5 - Deploy: FastAPI Recommendation Endpoint
Serves the Morenita Signals recommendation engine as a REST API.

Run:  uvicorn api.main:app --reload
Docs: http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager
from pathlib import Path
import sys

from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

sys.path.append(str(Path(__file__).resolve().parents[1]))  # project root on sys.path

from src.model.recommender import Recommender


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading model...")
    app.state.rec = Recommender.build()
    print(f"Model ready: {len(app.state.rec.df)} works.")
    yield


app = FastAPI(
    title="Morenita Signals",
    description="Finds related creative works across cultures and art forms.",
    lifespan=lifespan,
)


def _rec() -> Recommender:
    return app.state.rec


@app.get("/")
def root():
    rec = _rec()
    return {
        "message": "Morenita Signals API is running",
        "works": int(len(rec.df)),
        "collections": sorted(rec.df["collection"].unique().tolist()),
        "domains": rec.df["domain"].value_counts().to_dict(),
        "method": rec.default_method,
    }


@app.get("/search")
def search(q: str = Query(..., min_length=2), n: int = Query(10, ge=1, le=50)):
    """Find works whose title contains `q`."""
    return {"query": q, "results": _rec().search(q, n)}


@app.get("/recommend/{title}")
def get_recommendations(
    title: str,
    n: int = Query(5, ge=1, le=25),
    method: Optional[str] = Query(None, pattern="^(tags|meaning|blend)$"),
):
    """The closest works overall, each with the subjects it shares."""
    rec = _rec()
    results = rec.recommend(title, n, method=method)
    if results is None:
        raise HTTPException(status_code=404, detail=f"Work '{title}' not found. Try /search?q=...")
    return {"query": rec.card(title), "recommendations": results}


@app.get("/bridges/{title}")
def get_bridges(
    title: str,
    n: int = Query(5, ge=1, le=25),
    across: str = Query("collection", pattern="^(collection|domain)$"),
    method: Optional[str] = Query(None, pattern="^(tags|meaning|blend)$"),
):
    """The closest works from *other* collections (or, with across=domain,
    from another art form): links across cultures."""
    rec = _rec()
    results = rec.bridges(title, n, across, method)
    if results is None:
        raise HTTPException(status_code=404, detail=f"Work '{title}' not found. Try /search?q=...")
    return {"query": rec.card(title), "bridges": results}


_GRAPH_CACHE: dict = {}  # insertion-ordered, so the oldest entry is first


@app.get("/graph")
def get_graph(
    ref: str = Query(..., description="a work key or title"),
    n: int = Query(6, ge=1, le=12),
    method: Optional[str] = Query(None, pattern="^(tags|meaning|blend)$"),
):
    """A small constellation around one work, for the explorer."""
    # Each constellation takes ~30 similarity passes; cache them so going
    # back along the trail, or switching methods back and forth, is instant.
    cache = _GRAPH_CACHE
    key = (ref.strip().lower(), n, method)
    if key in cache:
        cache[key] = cache.pop(key)  # mark as recently used
        return cache[key]
    g = _rec().graph(ref, n=n, method=method)
    if g is not None:
        cache[key] = g
        while len(cache) > 256:
            cache.pop(next(iter(cache)))
    if g is None:
        raise HTTPException(status_code=404, detail=f"Work '{ref}' not found. Try /search?q=...")
    return g


WEB = Path(__file__).resolve().parents[1] / "web"


@app.get("/explore", include_in_schema=False)
def explore():
    """The Signals explorer: search a work and follow its links across art forms."""
    return FileResponse(WEB / "explore.html")
