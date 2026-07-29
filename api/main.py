""" 
Stage 5 - Deploy: FastAPI Reccomendation Endpoint 
Serves the Morenita Signals reccomendation engine as a REST API 
"""

from contextlib import asynccontextmanager 
from fastapi import FastAPI 
from pathlib import Path
import sys 

sys.path.append(str(Path(__file__).resolve().parents[1]))  # Add the src directory to sys.path

from src.model.recommender import load_data, build_tfidf_matrix, build_similarity_matrix, recommend

@asynccontextmanager
async def lifespan(app:FastAPI):
    print("Loading model...")
    df = load_data()
    tfidf_matrix = build_tfidf_matrix(df)
    cosine_sim = build_similarity_matrix(tfidf_matrix)
    app.state.df = df
    app.state.cosine_sim = cosine_sim
    print("Model ready.")
    yield  # Control returns to FastAPI, which starts the server   

app = FastAPI(title="Morenita Signals", lifespan=lifespan)
@app.get("/")
def root():
    return {"message": "Morenita Signals API is running"}


@app.get("/recommend/{title}")
def get_recommendations(title: str, n: int = 5):
    df = app.state.df
    cosine_sim = app.state.cosine_sim

    matches = df[df["title"].str.lower() == title.lower()]
    if matches.empty:
        return {"error": f"Book '{title}' not found."}

    idx = matches.index[0]
    scores = list(enumerate(cosine_sim[idx]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)[1:n+1]

    recommendations = [
        {"title": df["title"].iloc[i], "score": round(float(score), 3)}
        for i, score in scores
    ]


    

    return {"query": title, "recommendations": recommendations}
