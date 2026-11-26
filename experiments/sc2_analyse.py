"""SC2 analysis (PREREGISTRATION_SC2.md, amendment 2). 0 model calls. Written before any SC2 task was drawn.

    python experiments/sc2_analyse.py        # -> results/sc2.json

Reads bench/statebench_v1_SC2.jsonl and results/a7_results_SC2_<label>.jsonl (arms B2 and X5b).
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
R = os.path.join(ROOT, "results")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
import sc2_predictor as P                  # noqa: E402

ONE_KEY = {"INHERIT", "SCALE"}
FROZEN_PREDICTOR = "0c976ed0dba98c20f43a92eeeeba25ebf001519175811826843af204999068f3"


def poisson_interval(mu, z=1.96):
    """Approximate 95% interval for a Poisson count with mean mu (normal approximation with continuity)."""
    sd = math.sqrt(max(mu, 1e-9))
    return max(0, math.floor(mu - z * sd)), math.ceil(mu + z * sd)


def auc(scores, labels):
    pos = [s for s, y in zip(scores, labels) if y]; neg = [s for s, y in zip(scores, labels) if not y]
    if not pos or not neg:
        return None
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def stale_keys(task, k):
    kind, srcs, scan = P.parse(task["requests"][k])
    if not scan:
        return set()
    field, cond, val = scan
    init, cur = task["init"], task["truths"][k]
    objs = {x.split(".")[0] for x in list(init) + list(cur)}
    now = {o for o in objs if cur.get(f"{o}.{cond}") == val}
    start = {o for o in objs if init.get(f"{o}.{cond}") == val}
    return {f"{o}.{field}" for o in (now ^ start)} | {f"{o}.{field}" for o in now
                                                       if cur.get(f"{o}.{field}") != init.get(f"{o}.{field}")}


def wrong_keys(task, k, patch_text):
    """Keys a failed step got wrong: missing, extra or wrong value, from the step's final patch."""
    want = {x: v for x, v in task["truths"][k + 1].items() if task["truths"][k].get(x) != v}
    try:
        arr = json.loads(patch_text) if patch_text else []
    except ValueError:
        return set(want)
    got = {p.get("path", "").lstrip("/").replace("/", "."): str(p.get("value")) for p in arr if isinstance(p, dict)}
    return {x for x in set(want) | set(got) if want.get(x) != got.get(x)}


def main():
    assert P.frozen_hash() == FROZEN_PREDICTOR, "predictor changed after freezing"
    w = json.load(open(P.WEIGHTS))
    tasks = {json.loads(l)["seed"]: json.loads(l) for l in open(os.path.join(ROOT, "bench", "statebench_v1_SC2.jsonl"))}
    pred = {(s, k): P.predict(P.features(t, k)[1], w) for s, t in tasks.items() for k in range(len(t["requests"]))}
    kind = {(s, k): P.parse(t["requests"][k])[0] for s, t in tasks.items() for k in range(len(t["requests"]))}
    top10 = sorted(pred, key=pred.get, reverse=True)[:10]
    cells = {}
    for p in sorted(glob.glob(os.path.join(R, "a7_results_SC2_*.jsonl"))):
        label = re.match(r"a7_results_SC2_(.+)\.jsonl$", os.path.basename(p)).group(1)
        for line in open(p):
            r = json.loads(line)
            cells.setdefault(label, {}).setdefault(r["arm"], {})[r["seed"]] = r
    full = {l: a for l, a in cells.items() if all(len(a.get(x, {})) == 16 for x in ("B2", "X5b"))}
    out = {"top10_predicted": [list(x) for x in top10], "models": {}}
    fails_all, steps_all, scores, labels, stale_hits, wrong_total = {}, {}, [], [], 0, 0
    for l, arms in full.items():
        b2, x5 = arms["B2"], arms["X5b"]
        failed = {(s, st["step"]) for s, r in b2.items() for st in r["steps"] if not st["ok"] or not st["correct"]}
        for (s, k) in pred:
            kd = kind[(s, k)]
            steps_all[kd] = steps_all.get(kd, 0) + 1
            fails_all[kd] = fails_all.get(kd, 0) + ((s, k) in failed)
            scores.append(pred[(s, k)]); labels.append((s, k) in failed)
        for s, r in b2.items():
            for st in r["steps"]:
                if (not st["ok"] or not st["correct"]) and kind[(s, st["step"])] in ("FLOW", "REHOST"):
                    wk = wrong_keys(tasks[s], st["step"], st.get("ops"))
                    wrong_total += len(wk); stale_hits += len(wk & stale_keys(tasks[s], st["step"]))
        out["models"][l] = {
            "B2_exact": sum(r["success"] for r in b2.values()), "X5b_exact": sum(r["success"] for r in x5.values()),
            "B2_failed_steps": sorted([s, k + 1] for s, k in failed),
            "B2_failed_flow": sum(1 for s, k in failed if kind[(s, k)] == "FLOW"),
            "X5b_failed_steps": sum(1 for r in x5.values() for st in r["steps"] if not st["ok"] or not st["correct"]),
            "X5b_invalid_per_task": sum(r["invalid_ops"] for r in x5.values()) / 16,
            "predicted_expected_failures": round(sum(pred.values()), 2), "observed_failures": len(failed),
            "top10_hits": sorted([s, k + 1] for s, k in failed if (s, k) in top10)}
    rate = {k: fails_all[k] / steps_all[k] for k in steps_all if steps_all[k]}
    m = len(full)
    mu = m * sum(pred.values())
    lo, hi = poisson_interval(mu)
    obs = sum(v["observed_failures"] for v in out["models"].values())
    one_key = sum(fails_all.get(k, 0) for k in ONE_KEY) / max(sum(steps_all.get(k, 0) for k in ONE_KEY), 1)
    V = {
        "Q1_blind_exact": m > 0 and all(v["X5b_exact"] == 16 and v["X5b_failed_steps"] == 0 for v in out["models"].values()),
        "Q2_flow_rate_ge_5pct": m > 0 and rate.get("FLOW", 0) >= 0.05,
        "Q3_ordering": m > 0 and rate.get("FLOW", 0) > rate.get("REHOST", 0) > one_key,
        "Q5_invalid_le_1": m > 0 and all(v["X5b_invalid_per_task"] <= 1 for v in out["models"].values()),
        "Q6_predicted_count": m > 0 and lo <= obs <= hi,
        "Q7_ranking": m > 0 and (auc(scores, labels) or 0) >= 0.8 and any(v["top10_hits"] for v in out["models"].values()),
        "Q8_error_form_stale": wrong_total > 0 and stale_hits / wrong_total >= 0.5,
    }
    out.update({"complete_models": sorted(full), "rate_by_kind": rate, "one_key_rate": one_key,
                "predicted_interval_pooled": [lo, hi], "observed_pooled": obs, "auc_pooled": auc(scores, labels),
                "stale_share_of_wrong_keys": (stale_hits / wrong_total) if wrong_total else None, "verdicts": V})
    out["sha256"] = hashlib.sha256(json.dumps({k: out[k] for k in ("models", "verdicts", "rate_by_kind")},
                                              sort_keys=True, default=str).encode()).hexdigest()
    json.dump(out, open(os.path.join(R, "sc2.json"), "w"), indent=1, default=str)
    print(json.dumps({"verdicts": V, "complete_models": out["complete_models"], "sha256": out["sha256"]}, indent=1))


if __name__ == "__main__":
    main()
