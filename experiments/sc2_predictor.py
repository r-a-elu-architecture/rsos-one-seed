"""SC2 predictor: where one-call JSON Patch fails, computed from a task alone (0 model calls).

The law of the operation table (experiments/OPERATION_TABLE.md) as code. One-call JSON Patch (B2) writes every patch
of a task from the task's START state, so a step is hard when what it reads has been changed by earlier steps of the
same task and the model must replay them. For each step this module computes:

  scan        1 if the step scans the whole state (reassign_where / REHOST, derive_where / FLOW)
  stale       number of keys whose current value the step depends on and that differ from the start state:
                scan steps:   matched keys that arrived during the task + keys that left the match during the task
                other steps:  source keys changed since the start
  matched     keys the step changes (scan steps), else 1
  depth       position of the step in the task, 0..1

and a frozen logistic model p(fail) = sigmoid(w . f + b). Fit: `python experiments/sc2_predictor.py fit`
(writes experiments/sc2_predictor_weights.json); score a task file: `... rank bench/statebench_v1_SC2.jsonl`.
The weights file and this file are frozen together by sha256 before the SC2 tasks exist (PREREGISTRATION_SC2.md).
"""

import glob
import hashlib
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KEYRX = re.compile(r"^[a-z]+\.[a-z_]+$")
WEIGHTS = os.path.join(HERE, "sc2_predictor_weights.json")
FEATURES = ["scan", "log1p_stale", "log1p_matched", "nonscan_stale", "depth"]

OPS = [  # request templates of the generators (A1/A7b/SC1, plus FLOW for SC2) -> (kind, sources, scan spec)
    (r"^Set (\S+) to (\S+) plus 500\.$", lambda m: ("INHERIT", [m[2]], None)),
    (r"^Set (\S+) to (\S+) plus (\d), capped at 9\.$", lambda m: ("INHERIT", [m[2]], None)),
    (r"^Set (\S+) to (\S+) \+ (\S+), capped at 9\.$", lambda m: ("FUSE", [m[2], m[3]], None)),
    (r"^Set (\S+) to (\S+)\.$", lambda m: ("SET", [m[2]] if KEYRX.match(m[2]) else [], None)),
    (r"^Change the (\S+) of (\S+) to (\S+)\.$", lambda m: ("SET", [], None)),
    (r"^(\S+) needs (\S+) = (\S+) from now on\.$", lambda m: ("SET", [], None)),
    (r"^Increase (\S+) by (\d) \(cap at 9\)\.$", lambda m: ("INHERIT", [m[1]], None)),
    (r"^Double (\S+), capped at 9\.$", lambda m: ("SCALE", [m[1]], None)),
    (r"^Everything owned by (\S+) is now owned by (\S+)\.$", lambda m: ("REHOST", [], ("owner", "owner", m[1]))),
    (r"^Add a new line (\S+) = (\S+) at the end\.$", lambda m: ("SET", [], None)),
    (r"^Remove the line (\S+) entirely\.$", lambda m: ("DEL", [], None)),
    (r"^If (\S+) is (\S+), set (\S+) to (\S+); otherwise set it to (\S+)\.$", lambda m: ("ROUTE", [m[1]], None)),
    (r"^Make (\S+) equal to (\S+)\.$", lambda m: ("INHERIT", [m[2]], None)),
    (r"^Move every object owned by (\S+) (\d) cells? (?:right|up) \((\S+) plus \d, capped at 9\)\.$",
     lambda m: ("FLOW", [], (m[3], "owner", m[1]))),
]


def parse(req):
    r = req[len("Worker-computed: "):] if req.startswith("Worker-computed: ") else req
    for rx, f in OPS:
        m = re.match(rx, r)
        if m:
            return f(m)
    raise ValueError(req)


def features(task, k):
    """Features of step k (0-based) of a StateBench task dict (init, requests, truths)."""
    init, cur = task["init"], task["truths"][k]
    kind, srcs, scan = parse(task["requests"][k])
    n = len(task["requests"])
    if scan:
        field, cond_field, value = scan
        objs = {key.split(".")[0] for key in cur} | {key.split(".")[0] for key in init}
        now = {o for o in objs if cur.get(f"{o}.{cond_field}") == value and f"{o}.{field}" in cur}
        start = {o for o in objs if init.get(f"{o}.{cond_field}") == value}
        stale = len(now ^ start) + (sum(1 for o in now if cur.get(f"{o}.{field}") != init.get(f"{o}.{field}"))
                                    if field != cond_field else 0)
        f = {"scan": 1, "log1p_stale": math.log1p(stale), "log1p_matched": math.log1p(len(now)),
             "nonscan_stale": 0, "depth": k / max(n - 1, 1)}
    else:
        stale = sum(1 for s in srcs if cur.get(s) != init.get(s))
        f = {"scan": 0, "log1p_stale": 0.0, "log1p_matched": 0.0, "nonscan_stale": stale, "depth": k / max(n - 1, 1)}
    return kind, f


def dataset():
    """Every B2/B2s step of every A7/A8/SC1 result file, with its features and whether it failed."""
    tasks = {}
    for p in glob.glob(os.path.join(ROOT, "bench", "statebench_v1_*.jsonl")):
        for line in open(p):
            t = json.loads(line)
            tasks[(t["set"], t["seed"])] = t
    rows = []
    for p in sorted(glob.glob(os.path.join(ROOT, "results", "a7_results_*.jsonl"))):
        m = re.match(r"a7_results_(S1|S2|L1|L2|L3|SC1)_(.+)\.jsonl$", os.path.basename(p))
        if not m or m.group(2) == "off":
            continue
        for line in open(p):
            r = json.loads(line)
            if r["arm"] not in ("B2", "B2s") or r.get("tag") or (m.group(1), r["seed"]) not in tasks:
                continue
            t = tasks[(m.group(1), r["seed"])]
            for s in r["steps"]:
                kind, f = features(t, s["step"])
                rows.append({"set": m.group(1), "label": m.group(2), "seed": r["seed"], "step": s["step"],
                             "kind": kind, "fail": int(not s["ok"] or not s["correct"]), **f})
    return rows


def predict(f, w):
    z = w["bias"] + sum(w["coef"][k] * f[k] for k in FEATURES)
    return 1 / (1 + math.exp(-z))


def fit():
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    rows = dataset()
    X = np.array([[r[k] for k in FEATURES] for r in rows]); y = np.array([r["fail"] for r in rows])
    model = LogisticRegression(C=1.0, max_iter=2000).fit(X, y)
    w = {"features": FEATURES, "coef": dict(zip(FEATURES, map(float, model.coef_[0]))),
         "bias": float(model.intercept_[0]), "n_steps": len(rows), "n_fail": int(y.sum())}
    # out-of-sample check: leave one model out (fit on the others, score the held-out model)
    loo = {}
    for lab in sorted({r["label"] for r in rows}):
        tr = [i for i, r in enumerate(rows) if r["label"] != lab]; te = [i for i, r in enumerate(rows) if r["label"] == lab]
        if y[te].sum() == 0 or y[tr].sum() == 0:
            continue
        m2 = LogisticRegression(C=1.0, max_iter=2000).fit(X[tr], y[tr])
        loo[lab] = {"steps": len(te), "fails": int(y[te].sum()), "auc": round(float(roc_auc_score(y[te], m2.predict_proba(X[te])[:, 1])), 4)}
    w["leave_one_model_out"] = loo
    w["auc_in_sample"] = round(float(roc_auc_score(y, model.predict_proba(X)[:, 1])), 4)
    json.dump(w, open(WEIGHTS, "w"), indent=1)
    print(json.dumps(w, indent=1))


def rank(path, top=10):
    w = json.load(open(WEIGHTS))
    out = []
    for line in open(path):
        t = json.loads(line)
        for k in range(len(t["requests"])):
            kind, f = features(t, k)
            out.append((predict(f, w), t["seed"], k + 1, kind, t["requests"][k]))
    out.sort(reverse=True)
    return out[:top], out


def frozen_hash():
    h = hashlib.sha256()
    for p in (__file__, WEIGHTS):
        h.update(open(p, "rb").read())
    return h.hexdigest()


if __name__ == "__main__":
    if sys.argv[1] == "fit":
        fit()
    elif sys.argv[1] == "rank":
        top, _ = rank(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 10)
        for p, seed, step, kind, req in top:
            print(f"{p:.3f}  seed {seed} step {step}  {kind}  {req}")
    elif sys.argv[1] == "hash":
        print(frozen_hash())
