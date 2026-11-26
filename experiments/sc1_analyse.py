"""SC1 analysis (PREREGISTRATION_SC1.md, section 6). 0 model calls. Written before any SC1 model run.

    python experiments/sc1_analyse.py        # -> results/sc1.json

Reads results/a7_results_SC1_<label>.jsonl (arms B2 and X5b) and results/sc1_channel.json.
"""
import glob
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(os.path.dirname(HERE), "results")
DEP = {"INHERIT", "FUSE", "SCALE", "ROUTE", "REHOST"}
# P4: the five hand-over steps with the most objects to re-assign, published before the run (seed, 1-based step).
NAMED = [(913, 53), (908, 53), (913, 49), (909, 54), (913, 39)]
USD = {"mistral_large40": (1.36, 4.18)}          # A8 amendment 4 price sheet, USD per million input / output tokens


def rows():
    out = {}
    for p in sorted(glob.glob(os.path.join(R, "a7_results_SC1_*.jsonl"))):
        label = re.match(r"a7_results_SC1_(.+)\.jsonl$", os.path.basename(p)).group(1)
        for line in open(p):
            r = json.loads(line)
            out.setdefault(label, {}).setdefault(r["arm"], {})[r["seed"]] = r
    return out


def cell(rs, label):
    rs = list(rs.values())
    failed = [(r["seed"], s) for r in rs for s in r["steps"] if not s["ok"] or not s["correct"]]
    ex = sum(r["success"] for r in rs)
    tok = sum(r["billed_tok"] for r in rs)
    c = {"tasks": len(rs), "exact": ex, "failed_steps": len(failed),
         "failed_dependent": sum(1 for _, s in failed if s["kind"] in DEP),
         "failed_by_kind": {k: sum(1 for _, s in failed if s["kind"] == k) for k in sorted({s["kind"] for _, s in failed})},
         "failed_named_steps": sorted({(sd, s["step"] + 1) for sd, s in failed} & set(NAMED)),
         "invalid_ops": sum(r["invalid_ops"] for r in rs), "invalid_per_task": round(sum(r["invalid_ops"] for r in rs) / max(len(rs), 1), 3),
         "drifts": sum(len(r["drift"]) for r in rs),
         "healed_zero_call": sum(1 for r in rs for d in r["drift"] if d.get("healed_zero_call")),
         "tokens_per_correct": tok / ex if ex else None}
    if label in USD:
        pi, po = USD[label]
        usd = sum(r["in_tok"] * pi / 1e6 + r["out_tok"] * po / 1e6 for r in rs)
        c["usd_per_correct"] = usd / ex if ex else None
    return c


def main():
    T = {label: {arm: cell(rs, label) for arm, rs in arms.items()} for label, arms in rows().items()}
    full = {l: a for l, a in T.items() if all(a.get(x, {}).get("tasks") == 16 for x in ("B2", "X5b"))}
    ch = json.load(open(os.path.join(R, "sc1_channel.json")))
    V = {}
    V["P1_blind_exact"] = bool(full) and all(a["X5b"]["exact"] == 16 for a in full.values())
    V["P2_json_patch_fails"] = any(a["B2"]["exact"] <= 15 for a in full.values())
    V["P3_failures_state_dependent"] = (all(a["B2"]["failed_steps"] == a["B2"]["failed_dependent"] for a in full.values())
                                        and all(a["X5b"]["failed_steps"] == 0 for a in full.values()))
    V["P4_named_handover"] = any(a["B2"]["failed_named_steps"] for a in full.values())
    V["P5_cost"] = bool(full) and all(
        a["B2"]["tokens_per_correct"] and a["X5b"]["tokens_per_correct"] <= 0.7 * a["B2"]["tokens_per_correct"]
        and (a["B2"].get("usd_per_correct") is None or a["X5b"]["usd_per_correct"] <= 0.7 * a["B2"]["usd_per_correct"])
        for a in full.values())
    V["P6_drift_zero_call"] = bool(full) and all(a[x]["healed_zero_call"] == a[x]["drifts"] > 0
                                                 for a in full.values() for x in ("B2", "X5b"))
    bpe = ch["ratios"].get("o200k_tokens")
    route = ch["by_operation"].get("ROUTE", {})
    V["P7_channel_bpe"] = (None if bpe is None else
                           bpe["R_vs_P"] <= 0.6 and route["R_rsos_plus_digest"]["o200k_tokens"]
                           > route["P_json_patch_plus_digest"]["o200k_tokens"])
    out = {"cells": T, "complete_models": sorted(full), "verdicts": V, "channel_sha256": ch["sha256"],
           "channel_ratios": ch["ratios"]}
    out["sha256"] = hashlib.sha256(json.dumps({k: out[k] for k in ("cells", "verdicts")}, sort_keys=True,
                                              default=str).encode()).hexdigest()
    json.dump(out, open(os.path.join(R, "sc1.json"), "w"), indent=1, default=str)
    print(json.dumps({"verdicts": V, "complete_models": out["complete_models"], "sha256": out["sha256"]}, indent=1))


if __name__ == "__main__":
    main()
