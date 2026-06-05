import json 
from pathlib import Path

import pandas as pd 

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" 
CLEAN_DIR = Path(__file__).resolve().parents[2] / "data" / "clean"

def load_raw() -> list [dict]:
    all_docs = [] 
    """
    loop over every .json file in RAW_DIR 
    open each file, load the JSON, extend all_docs 
    """
    for file in RAW_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_docs.extend(data)
    return all_docs 

import pandas as pd

def make_dataframe(docs: list[dict]) -> pd.DataFrame:
    """
    Convert list of dicts to a DataFrame and do some basic cleaning.
    """
    for doc in docs:
        doc["key"] = doc.get("key", "")
        doc["title"] = doc.get("title", "")
        doc["author_name"] = doc.get("author_name", [])
        doc["subject"] = doc.get("subject", [])
        doc["first_publish_year"] = doc.get("first_publish_year", None)
        doc["language"] = doc.get("language", [])
        doc["edition_count"] = doc.get("edition_count", 0)
    return pd.DataFrame(docs)

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df["author_name"] = df["author_name"].apply(lambda x: x[0] if isinstance(x, list) and x else None)
    df["language"] = df["language"].apply(lambda x: x[0] if isinstance(x, list) and x else None)
    df["first_publish_year"] = df["first_publish_year"].fillna(0).astype(int)
    df["title"] = df["title"].fillna("")
    df["key"] = df["key"].fillna("")
    return df

def save_clean(df:pd.DataFrame) -> Path: 
    filepath = CLEAN_DIR / "clean.parquet" 
    df.to_parquet(filepath, index=False)
    print (f"Saved {len(df)} records to {filepath}")
    return filepath

def main():
    docs = load_raw()
    df = make_dataframe(docs)
    df = normalize(df)
    save_clean(df) 

if __name__ == "__main__":
    main()