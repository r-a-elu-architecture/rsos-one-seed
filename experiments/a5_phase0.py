"""A5 Phase 0: cache diagnosis, fix check, and the offline B1 estimate (no task calls). BRIEF_A5_COST.md.

    python experiments/a5_phase0.py probe      # ~40 tiny calls: legacy vs fixed call, scaffold, threshold, TTL
    python experiments/a5_phase0.py estimate   # offline: reprice the recorded A3b and A4 H-dragon transcripts

Outputs: results/a5_cache_diagnosis.json, results/a5_b1_offline.json.
"""

import json
import os
import random
import statistics as stt
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a5_llm as L                      # noqa: E402
import a5_cost as C                     # noqa: E402

ROOT = os.path.dirname(HERE)
R = os.path.join(ROOT, "results")


def load_hd(path, cond="Hd"):
    out = []
    for line in open(path):
        d = json.loads(line)
        if d["cond"] == cond and d.get("tag") in (None,):
            out.append(d)
    return out


def systems():
    import a1_agents as A
    import a4_latent as A4
    base = dict(A.SYS)
    s4 = {"planner": A4.PLANNER_A4, "checker": A4.CHECKER_A4, "worker": A.SYS["worker"]}
    return {s[:40]: s for s in list(base.values()) + list(s4.values())}


def probe():
    out = {}
    nulls = {"legacy": [], "fixed": []}
    for mode in nulls:
        for i in range(3):
            _, _, r = L.raw_call("x", f"Reply OK. {i}", legacy=(mode == "legacy"))
            nulls[mode].append(r)
    out["null_calls"] = nulls
    out["scaffold_tokens"] = {m: stt.mean(r["in"] + r["cache_w"] + r["cache_r"] for r in v) for m, v in nulls.items()}
    # recorded H-dragon prompts, called both ways
    sysm = systems()
    rec = []
    for path in ("a3b_transcripts_hd.jsonl", "a4_transcripts.jsonl"):
        t = load_hd(os.path.join(R, path))[0]
        for c in t["calls"][:6]:
            s = sysm[c["system"]]
            row = {"source": path, "seed": t["seed"], "role_sys": c["system"],
                   "recorded": {k: c[k] for k in ("in", "cache_w", "cache_r", "out", "cost")}}
            for mode in ("legacy", "fixed"):
                _, _, r = L.raw_call(s, c["prompt"], legacy=(mode == "legacy"))
                row[mode] = r
            rec.append(row)
    out["recorded_prompt_calls"] = rec
    tot = lambda r: r["in"] + r["cache_w"] + r["cache_r"]          # noqa: E731
    out["legacy_minus_fixed_tokens_per_call"] = stt.mean(tot(x["legacy"]) - tot(x["fixed"]) for x in rec)
    out["recorded_minus_legacy_now"] = stt.mean(tot(x["recorded"]) - tot(x["legacy"]) for x in rec)
    out["legacy_ttl"] = {"1h_tokens": sum(x["legacy"]["cache_w1h"] for x in rec),
                         "5m_tokens": sum(x["legacy"]["cache_w5m"] for x in rec)}
    out["fixed_ttl"] = {"1h_tokens": sum(x["fixed"]["cache_w1h"] for x in rec),
                        "5m_tokens": sum(x["fixed"]["cache_w5m"] for x in rec)}
    out["reads_recorded_prompts"] = {m: sum(x[m]["cache_r"] for x in rec) for m in ("legacy", "fixed")}
    # threshold: when does the system region start to be read? (fixed call, two calls per size, varying tail)
    thr = []
    base = "You are the PLANNER in a three-agent pipeline that edits a configuration state. "
    for pad in (0, 40, 60, 90):
        sp = base + " ".join(f"Note {i}: be exact." for i in range(pad))
        rr = []
        for i in range(2):
            p = (f"Change request: set k{random.randint(0, 10**6)}.f to {i}.\n\nState:\n" +
                 "\n".join(f"k{j}.f = {random.randint(0, 99)}" for j in range(30)) + "\nReply OK only.")
            _, _, r = L.raw_call(sp, p)
            rr.append({k: r[k] for k in ("in", "cache_w", "cache_r", "out")})
        thr.append({"pad_notes": pad, "calls": rr})
    out["threshold_probe"] = thr
    # cost cross-check: CLI total_cost_usd vs tokens x run-time sheet
    P = C.prices()["sheets"]["haiku-5-5"]
    calls = [x[m] for x in rec for m in ("legacy", "fixed")] + nulls["legacy"] + nulls["fixed"]
    diffs = [abs(C.call_cost(r, P, "billed") - r["cost"]) for r in calls]
    out["cost_crosscheck"] = {"calls": len(calls), "max_abs_diff_usd": max(diffs),
                              "pass": max(diffs) < 1e-9}
    json.dump(out, open(os.path.join(R, "a5_cache_diagnosis.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("recorded_prompt_calls", "null_calls")}, indent=1))


def estimate():
    """Offline B1: the recorded H-dragon transcripts with the fix simulated (no calls).

    Per call, content tokens = recorded input tokens - recorded-session scaffold. Fixed call (basis 'cli'):
    content + fixed scaffold, all written to the 5-minute cache, none read (the measured behaviour of the fixed call
    for prompts whose static system region is below the 512-token minimum). API-optimal (basis 'api'): content at
    base input price. Output tokens as recorded."""
    diag = json.load(open(os.path.join(R, "a5_cache_diagnosis.json")))
    sc_leg, sc_fix = diag["scaffold_tokens"]["legacy"], diag["scaffold_tokens"]["fixed"]
    shift = diag["recorded_minus_legacy_now"]          # recorded session vs this session's legacy call
    sc_rec = sc_leg + shift
    prices = C.prices()
    res = {"scaffold_recorded_session": sc_rec, "scaffold_fixed": sc_fix, "sets": {}}
    for name, path in (("S1", "a3b_results_hd.jsonl"), ("S2", "a4_results.jsonl")):
        rows = [json.loads(x) for x in open(os.path.join(R, path))]
        rows = [r for r in rows if r["cond"] == "Hd"]
        per = []
        for r in rows:
            calls = []
            for c in r["per_call"]:
                content = c["in"] + c["cache_w"] + c["cache_r"] - sc_rec
                calls.append({"role": c["role"], "content": content, "out": c["out"],
                              "rec": {"in": c["in"], "cache_w": c["cache_w"], "cache_r": c["cache_r"], "out": c["out"]}})
            per.append({"seed": r["seed"], "calls": calls, "recorded_cost_usd": r["cost_usd"]})
        sheets = {}
        for sh, P in prices["sheets"].items():
            api = [sum(C.price_tokens({"in": c["content"], "out": c["out"]}, P) for c in t["calls"]) for t in per]
            cli = [sum(C.price_tokens({"cache_w5m": c["content"] + sc_fix, "out": c["out"]}, P) for c in t["calls"])
                   for t in per]
            rec = [sum(C.price_tokens({"in": c["rec"]["in"], "cache_w1h": c["rec"]["cache_w"],
                                       "cache_r": c["rec"]["cache_r"], "out": c["out"]}, P) for c in t["calls"])
                   for t in per]
            sheets[sh] = {"api_mean_usd": stt.mean(api), "cli_mean_usd": stt.mean(cli),
                          "as_recorded_mean_usd": stt.mean(rec),
                          "fix_gain_cli": stt.mean(rec) / stt.mean(cli), "fix_gain_api": stt.mean(rec) / stt.mean(api)}
        n = len(per)
        res["sets"][name] = {
            "tasks": n, "seeds": [t["seed"] for t in per],
            "calls_mean": sum(len(t["calls"]) for t in per) / n,
            "content_in_mean": sum(c["content"] for t in per for c in t["calls"]) / n,
            "out_mean": sum(c["out"] for t in per for c in t["calls"]) / n,
            "out_by_role": {ro: sum(c["out"] for t in per for c in t["calls"] if c["role"] == ro) / n
                            for ro in ("planner", "worker", "checker")},
            "content_by_role": {ro: sum(c["content"] for t in per for c in t["calls"] if c["role"] == ro) / n
                                for ro in ("planner", "worker", "checker")},
            "recorded_cli_cost_usd_mean": sum(t["recorded_cost_usd"] for t in per) / n,
            "sheets": sheets}
    json.dump(res, open(os.path.join(R, "a5_b1_offline.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"probe": probe, "estimate": estimate}[sys.argv[1]]()
