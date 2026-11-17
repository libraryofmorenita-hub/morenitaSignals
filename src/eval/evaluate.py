"""
src/eval/evaluate.py: a scorecard for Signals.

    python -m src.eval.evaluate            # every method available
    python -m src.eval.evaluate --k 5 --sample 400

Three numbers per method:
  probes     share of hand-written checks (probes.json) that pass: one of the
             top-k cross-art-form bridges lands in an expected collection
  coverage   share of sampled works with at least one bridge strong enough
             to show (above that method's MIN_SCORE)
  diversity  of all bridges shown for the sample, the share pointing to a
             different collection than the query: links across cultures
             rather than more of the same

Meaning and blend need data/clean/embeddings.npy, so on a machine without
it only "tags" is scored.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from src.model.recommender import Recommender

PROBES = Path(__file__).with_name("probes.json")


def run_probes(rec: Recommender, method: str, k: int) -> tuple[int, int, list[dict]]:
    probes = json.loads(PROBES.read_text())["probes"]
    passed, rows = 0, []
    for p in probes:
        idx = rec.find(p["query"])
        if idx is None:
            rows.append({**p, "result": "missing"})
            continue
        got = rec._neighbors(idx, k, "domain", method)
        hit = next((g for g in got if g["collection"] in p["expect"]), None)
        passed += bool(hit)
        rows.append({**p, "result": "pass" if hit else "fail",
                     "top": [(g["title"], g["collection"], g["score"]) for g in got[:3]]})
    scored = sum(r["result"] != "missing" for r in rows)
    return passed, scored, rows


def coverage(rec: Recommender, method: str, k: int, sample: int, seed: int = 0) -> tuple[float, float]:
    rnd = random.Random(seed)
    idxs = rnd.sample(range(len(rec.df)), min(sample, len(rec.df)))
    has, cross, total = 0, 0, 0
    for i in idxs:
        got = rec._neighbors(i, k, "domain", method)
        has += bool(got)
        total += len(got)
        cross += sum(g["collection"] != rec.df.at[i, "collection"] for g in got)
    return has / len(idxs), (cross / total if total else 0.0)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--sample", type=int, default=300)
    ap.add_argument("--verbose", action="store_true", help="show each probe's top bridges")
    a = ap.parse_args(argv)

    rec = Recommender.build()
    methods = ["tags"] + (["meaning", "blend"] if rec.embeddings is not None else [])
    print(f"{len(rec.df)} works. Scoring {', '.join(methods)} at k={a.k}.\n")
    print(f"{'method':<9}{'probes':>10}{'coverage':>11}{'diversity':>11}")
    detail = {}
    for m in methods:
        p, n, rows = run_probes(rec, m, a.k)
        cov, div = coverage(rec, m, a.k, a.sample)
        detail[m] = rows
        print(f"{m:<9}{f'{p}/{n}':>10}{cov:>10.0%}{div:>11.0%}")
    missing = [r["query"] for r in detail[methods[0]] if r["result"] == "missing"]
    if missing:
        print("\nNot in the data (edit probes.json or collect more):", ", ".join(missing))
    for m in methods:
        fails = [r for r in detail[m] if r["result"] == "fail"]
        if fails:
            print(f"\n{m}: failing probes")
            for r in fails:
                print(f"  {r['query']}  (wanted {', '.join(r['expect'])})")
                if a.verbose:
                    for t, c, s in r["top"]:
                        print(f"      {s:.2f}  {t}  [{c}]")
    return detail


if __name__ == "__main__":
    main()
