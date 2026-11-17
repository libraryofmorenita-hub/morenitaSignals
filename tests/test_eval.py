from src.eval import evaluate


def test_scorecard_runs_and_probes_resolve():
    detail = evaluate.main(["--sample", "40"])
    rows = detail["tags"]
    assert rows and all(r["result"] in ("pass", "fail", "missing") for r in rows)
    # most probes should point at works that exist in the data
    assert sum(r["result"] != "missing" for r in rows) >= len(rows) - 2
