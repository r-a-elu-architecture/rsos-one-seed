"""Score any system on RSOS-StateBench v1. 0 model calls.

Submission: JSONL, one line per task: {"set": "S1", "seed": 100, "final_state": {...}, "calls": 2,
"input_tokens": 2400, "output_tokens": 1900, "cost_usd": 0.0012}  (calls, tokens and cost optional).

    python bench/score.py my_results.jsonl [--name "LangGraph + GPT-x, one-call JSON"]
"""
import argparse
import hashlib
import json
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SETS = ("S1", "S2", "L1", "L2", "L3", "SC1")


def tasks():
    out = {}
    for s in SETS:
        for line in open(os.path.join(HERE, f"statebench_v1_{s}.jsonl")):
            t = json.loads(line)
            out[(t["set"], t["seed"])] = t
    return out


def score(path):
    T = tasks()
    subs = {}
    for line in open(path):
        r = json.loads(line)
        subs[(r["set"], int(r["seed"]))] = r
    rows = {}
    for s in sorted({k[0] for k in subs}):
        keys = [k for k in T if k[0] == s]
        got = [subs.get(k) for k in keys]
        exact = sum(1 for k, g in zip(keys, got) if g and g["final_state"] == T[k]["final"])
        acc = []
        for k, g in zip(keys, got):
            truth, fin = T[k]["final"], (g or {}).get("final_state", {})
            ks = set(truth) | set(fin)
            acc.append(sum(fin.get(x) == truth.get(x) for x in ks) / len(ks))
        costs = [g["cost_usd"] for g in got if g and "cost_usd" in g]
        rows[s] = {"tasks": len(keys), "submitted": sum(1 for g in got if g), "exact": exact,
                   "line_acc": round(st.mean(acc), 4),
                   "calls": round(st.mean(g["calls"] for g in got if g and "calls" in g), 3)
                   if any(g and "calls" in g for g in got) else None,
                   "cost_per_correct_usd": (round(sum(costs) / exact, 6) if exact and len(costs) == len(keys)
                                            else None)}
    rows["submission_sha256"] = hashlib.sha256(open(path, "rb").read()).hexdigest()
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("submission")
    ap.add_argument("--name", default="")
    a = ap.parse_args()
    out = score(a.submission)
    out["name"] = a.name
    print(json.dumps(out, indent=1))
