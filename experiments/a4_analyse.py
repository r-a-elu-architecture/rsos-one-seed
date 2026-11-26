"""A4 analysis: L1-L4 (PREREGISTRATION_A4.md) -> results/a4_latent.json.

Reads results/a4_runs.json (or a4_results.jsonl) and results/a4_transcripts.jsonl. Tasks are regenerated with
a4_latent.make_task (deterministic). BPE (o200k) is required.
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a1_agents as A                      # noqa: E402
import a3b_hologram as H                   # noqa: E402
import a4_latent as L                      # noqa: E402
from a1_analyse import mean                # noqa: E402
from common import bootstrap_ci, save      # noqa: E402

if H._BPE is None:
    sys.exit("a4_analyse: tiktoken (o200k_base) is required")

R = A.ROOT
EDGE = {("planner", "worker"): "instruction", ("worker", "checker"): "edits", ("checker", "worker"): "door",
        ("checker", "planner"): "forward", ("planner", "checker"): "forward"}
FROZEN = ["experiments/a1_agents.py", "experiments/a3_run.py", "experiments/a3b_hologram.py",
          "experiments/a3b_hdragon.py"]


def edge_of(m):
    return "heal" if m["kind"] == "heal" else EDGE.get((m["from"], m["to"]), "other")


def _toks(s):
    # analysis correction 1: strip sentence punctuation, so 'warn.' counts as 'warn' (first pass: 41 false leaks)
    return {t.rstrip(".") for t in re.findall(r"[\w.-]+", s)}


def leak(c, instr, req):
    toks = _toks(instr)
    if c["op"] == "xref":
        l1, l2 = re.search(r"set \S+ to (\w+); otherwise set it to (\w+)", c["text"]).groups()
        return (l1 in toks) != (l2 in toks)
    rq = _toks(req)
    return c["f_true"] in toks and c["f_true"] not in rq


def compute_outcomes(run, task, instrs):
    out = []
    for c in task["computes"]:
        v = run["final_state"].get(c["target"])
        cls = "correct" if v == c["f_true"] else ("traced" if c["f_wrong"] is not None and v == c["f_wrong"]
                                                  else "other_wrong")
        st = c["step"]
        grp = "clean" if c["kind"] == "clean" else ("same_step" if st in (4, 8, 12) else "later")
        out.append({"step": st, "group": grp, "op": c["op"], "target": c["target"], "true": c["f_true"],
                    "drifted": c["f_wrong"], "got": v, "class": cls,
                    "leak": leak(c, instrs[st], task["requests"][st]) if instrs else None,
                    "instruction": instrs[st] if instrs else None})
    return out


def summarise(rs, trans):
    ev = [e for r in rs for e in r["drift"]]
    edges = {}
    bpe, chan = [], []
    for r in rs:
        t = trans[(r["cond"], r["seed"])]
        b = 0
        for m in t["msgs"]:
            x = edges.setdefault(edge_of(m), [0, 0]); x[0] += m["tok"]; bb = H.bpe(m["text"]); x[1] += bb; b += bb
        bpe.append(b); chan.append(r["channel_tok"])
        assert sum(m["tok"] for m in t["msgs"]) == r["channel_tok"]
    co = [o for r in rs for o in r["computes"]]

    def cnt(group=None, cls=None):
        return sum(1 for o in co if (group is None or o["group"] == group) and (cls is None or o["class"] == cls))
    comp = {g: {k: cnt(g, k) for k in ("correct", "traced", "other_wrong")} | {"n": cnt(g)}
            for g in ("clean", "same_step", "later")}
    comp["drift_reading"] = {k: comp["same_step"][k] + comp["later"][k] for k in comp["same_step"]}
    comp["leaks"] = sum(1 for o in co if o["leak"])
    comp["leaks_drift_reading"] = sum(1 for o in co if o["leak"] and o["group"] != "clean")
    comp["traced_with_leak"] = sum(1 for o in co if o["leak"] and o["class"] == "traced")
    comp["correct_drift_reading_with_leak"] = sum(1 for o in co if o["leak"] and o["class"] == "correct"
                                                  and o["group"] != "clean")
    return {
        "tasks": len(rs), "success": sum(r["success"] for r in rs),
        "replica_success": sum(r["replica_success"] for r in rs),
        "wrong_final_lines": sum(len(r["final_errors"]) for r in rs),
        "tasks_with_traced_error": sum(1 for r in rs if any(o["class"] == "traced" for o in r["computes"])),
        "channel_tok_mean": mean(chan), "channel_tok_ci": bootstrap_ci(chan),
        "channel_bpe_mean": mean(bpe), "channel_bytes_mean": mean([r["channel_bytes"] for r in rs]),
        "edges_tok_bpe_per_task": {k: [v[0] / len(rs), v[1] / len(rs)] for k, v in sorted(edges.items())},
        "billed_tok_mean": mean([r["billed_tok"] for r in rs]), "out_tok_mean": mean([r["out_tok"] for r in rs]),
        "calls_mean": mean([r["n_calls"] for r in rs]), "wall_sec_mean": mean([r["wall_sec"] for r in rs]),
        "cost_usd_total": sum(r["cost_usd"] for r in rs), "steps_failed": sum(r["steps_failed"] for r in rs),
        "drift_events": len(ev), "drift_healed": sum(e["healed"] for e in ev),
        "drift_healed_zero_call": sum(e["healed_zero_call"] for e in ev),
        "drift_in_authoritative_final": sum(e["silent_in_final"] for e in ev),
        "drift_in_any_copy_final": sum(e["in_any_copy_final"] for e in ev),
        "computes": comp,
        "final_errors": {r["seed"]: r["final_errors"] for r in rs},
        "replayed_runs": sum(1 for r in rs if r.get("replayed")),
    }


def main():
    L.patch()
    fp = os.path.join(R, "results", "a4_results.jsonl")
    runs = {}
    for line in open(fp):
        r = json.loads(line); runs[(r["cond"], r["seed"])] = r
    trans = {}
    for line in open(L.TRANS):
        t = json.loads(line); trans[(t["cond"], t["seed"])] = t
    tasks = {s: L.make_task(s) for s in L.SEEDS}
    for (c, s), r in runs.items():
        pl = [x for x in trans[(c, s)]["calls"] if x["system"] == A.SYS["planner"][:40]]
        assert len(pl) == A.STEPS, (c, s, len(pl))
        r["computes"] = compute_outcomes(r, tasks[s], [x["text"].strip() for x in pl])
    conds = [c for c in L.CONDS if any(k[0] == c for k in runs)]
    T = {c: summarise([runs[(c, s)] for s in L.SEEDS if (c, s) in runs], trans) for c in conds}
    diff = subprocess.run(["git", "-C", R, "diff", "main", "--"] + FROZEN, capture_output=True, text=True).stdout
    preds = {}
    if "D" in T:
        preds["L1"] = {"D_exact": T["D"]["success"], "limit": 12, "pass": T["D"]["success"] <= 12}
    if "Hd" in T and "P" in T:
        preds["L2"] = {c: {"exact": T[c]["success"], "replica": T[c]["replica_success"]} for c in ("Hd", "P")}
        preds["L2"]["pass"] = all(T[c]["success"] >= 15 and T[c]["replica_success"] == 16 for c in ("Hd", "P"))
    if "Hd" in T and "D" in T:
        td, th = T["D"]["computes"]["drift_reading"]["traced"], T["Hd"]["computes"]["drift_reading"]["traced"]
        preds["L3"] = {"D_traced": td, "Hd_traced": th, "pass": td >= 10 and th == 0}
        preds["L4"] = {"Hd": T["Hd"]["channel_tok_mean"], "D": T["D"]["channel_tok_mean"],
                       "bpe_Hd": T["Hd"]["channel_bpe_mean"], "bpe_D": T["D"]["channel_bpe_mean"],
                       "ratio": T["Hd"]["channel_tok_mean"] / T["D"]["channel_tok_mean"],
                       "bpe_ratio": T["Hd"]["channel_bpe_mean"] / T["D"]["channel_bpe_mean"],
                       "pass": T["Hd"]["channel_tok_mean"] <= T["D"]["channel_tok_mean"]
                       and T["Hd"]["channel_bpe_mean"] <= T["D"]["channel_bpe_mean"]}
    replay = json.load(open(os.path.join(R, "results", "a4_replay_check.json")))
    per_compute = {c: {s: runs[(c, s)]["computes"] for s in L.SEEDS if (c, s) in runs} for c in conds}
    payload = {"model": A.MODEL, "seeds": L.SEEDS, "conds": conds, "frozen_files_diff_vs_main_empty": diff == "",
               "replay_check": replay, "tables": T, "predictions": preds, "per_compute": per_compute,
               "planner_system": A.SYS["planner"]}
    path, dig = save("a4_latent", payload)
    print(json.dumps({"tables": {c: {k: v for k, v in T[c].items() if k != "final_errors"} for c in T},
                      "predictions": preds}, indent=1, default=str))
    print(path, dig)


if __name__ == "__main__":
    main()
