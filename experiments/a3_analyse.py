"""A3 analysis: R1-R4 from results/a3_runs.json + results/a3_transcripts.jsonl -> results/a3_head_to_head.json.

Pre-registration: experiments/PREREGISTRATION_A3.md. D and E are Slipstream-style / ACCP-style re-implementations.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a1_agents as A                      # noqa: E402
from a1_analyse import recovery as a1_recovery, scaffold_sub, mean, FRACS   # noqa: E402
from common import save, bootstrap_ci      # noqa: E402

CONDS = ["P", "A", "D", "E"]
SETS = {"all": None, "a1_seeds_100_107": range(100, 108), "new_seeds_300_307": range(300, 308)}


def recovery(run):
    """A1's recovery measure, corrected for D/E: their checker -> worker channel also carries ACCEPT/ACK messages,
    so a checker -> worker message counts as a rejection only if no checker -> planner forward follows in the same
    (step, attempt). For A (rejections only on that edge) and P (heal messages) this equals A1's measure."""
    if run["cond"] in ("P", "A"):
        return a1_recovery(run)
    out = []
    for e in run["drift"]:
        st = e["step"]
        msgs = [m for m in run["per_msg"] if m["step"] == st]
        fwd = {m["attempt"] for m in msgs if m["from"] == "checker" and m["to"] == "planner"}
        rej = [m for m in msgs if m["from"] == "checker" and m["to"] == "worker" and m["attempt"] not in fwd]
        ch = sum(m["tok"] for m in msgs if m["attempt"] >= 1) + sum(m["tok"] for m in rej if m["attempt"] == 0)
        calls = [c for c in run["per_call"] if c["step"] == st and c["attempt"] >= 1]
        out.append({"caught": e["caught"], "chan": ch,
                    "billed": sum(c["in"] + c["cache_w"] + c["cache_r"] + c["out"] for c in calls),
                    "sec": sum(c["sec"] for c in calls)})
    return out


def strict_ok(cond, cut):
    """True if the receiver's strict decoder accepts the (possibly cut) worker -> checker message."""
    try:
        if cond == "P":
            rows = cut.split("\n")
            return rows[-1].startswith("=") and len(rows[-1]) == 9
        if cond == "A":
            json.loads(cut)
        elif cond == "D":
            A.d_decode(cut, strict=True)
        else:
            A.e_decode(cut, strict=True)
        return True
    except Exception:  # noqa: BLE001
        return False


def truncation(trans):
    res = {c: {f: {"detected": 0, "silent_wrong": 0, "correct": 0} for f in FRACS} for c in CONDS}
    cost = {c: [] for c in CONDS}
    for t in trans:
        c = t["cond"]
        for m in t["msgs"]:
            if not (m["from"] == "worker" and m["to"] == "checker" and m["kind"] == "msg"):
                continue
            txt = m["text"]
            for f in FRACS:
                cut = txt[:int(len(txt) * (1 - f))]
                key = ("correct" if cut == txt else "silent_wrong") if strict_ok(c, cut) else "detected"
                res[c][f][key] += 1
            cost[c].append(A.ntok(txt))
    return res, cost


def summarise(rs, sc):
    ev = [e for r in rs for e in r["drift"]]
    rec = [(x, e) for r in rs for x, e in zip(recovery(r), r["drift"])]
    healed = [x for x, e in rec if e["healed"]]
    return {
        "tasks": len(rs), "success": sum(r["success"] for r in rs),
        "replica_success": sum(r["replica_success"] for r in rs),
        "line_acc_mean": mean([r["line_acc"] for r in rs]),
        "wrong_final_lines": sum(len(r["final_errors"]) for r in rs),
        "channel_tok_mean": mean([r["channel_tok"] for r in rs]),
        "channel_tok_ci": bootstrap_ci([r["channel_tok"] for r in rs]),
        "channel_bytes_mean": mean([r["channel_bytes"] for r in rs]),
        "billed_tok_mean": mean([r["billed_tok"] for r in rs]),
        "billed_minus_scaffold_mean": mean([scaffold_sub(r, sc) for r in rs]),
        "out_tok_mean": mean([r["out_tok"] for r in rs]),
        "calls_mean": mean([r["n_calls"] for r in rs]),
        "wall_sec_mean": mean([r["wall_sec"] for r in rs]),
        "cost_usd_total": sum(r["cost_usd"] for r in rs),
        "steps_failed": sum(r["steps_failed"] for r in rs),
        "drift_events": len(ev),
        "drift_healed": sum(e["healed"] for e in ev),
        "drift_healed_zero_call": sum(e["healed_zero_call"] for e in ev),
        "drift_in_authoritative_final": sum(e["silent_in_final"] for e in ev),
        "drift_in_any_copy_final": sum(e["in_any_copy_final"] for e in ev),
        "recovery_chan_per_healed": mean([x["chan"] for x in healed]),
        "recovery_billed_per_healed": mean([x["billed"] for x in healed]),
        "recovery_total_per_healed": mean([x["chan"] + x["billed"] for x in healed]),
        "recovery_sec_per_healed": mean([x["sec"] for x in healed]),
        "final_errors": {r["seed"]: r["final_errors"] for r in rs},
    }


def ratio(a, b):
    return None if a is None or not b else a / b


def main():
    R = json.load(open(os.path.join(A.ROOT, "results", "a3_runs.json")))
    trans = [json.loads(l) for l in open(os.path.join(A.ROOT, "results", "a3_transcripts.jsonl"))]
    sc, runs = R["scaffold"], R["runs"]
    tables = {}
    for name, seeds in SETS.items():
        tables[name] = {c: summarise([r for r in runs if r["cond"] == c and (seeds is None or r["seed"] in seeds)], sc)
                        for c in CONDS}
    T = tables["all"]
    lo = min(T["D"]["channel_tok_mean"], T["E"]["channel_tok_mean"])
    preds = {
        "R1": {"P": T["P"]["channel_tok_mean"], "D": T["D"]["channel_tok_mean"], "E": T["E"]["channel_tok_mean"],
               "P_over_min_DE": T["P"]["channel_tok_mean"] / lo,
               "D_with_table": T["D"]["channel_tok_mean"] + A.ntok(A.UCR_TABLE),
               "pass": T["P"]["channel_tok_mean"] <= 1.2 * lo},
        "R2": {c: f"{T[c]['drift_healed_zero_call']}/{T[c]['drift_events']}" for c in CONDS} | {
            "pass": T["P"]["drift_healed_zero_call"] == T["P"]["drift_events"]
            and all(T[c]["drift_healed_zero_call"] < T["P"]["drift_healed_zero_call"] for c in "DE")},
        "R3": {c: T[c]["success"] for c in CONDS} | {
            "pass": all(T["P"]["success"] >= T[c]["success"] for c in "DE")},
    }
    r4 = {}
    for c in "DE":
        rt = ratio(T["P"]["recovery_total_per_healed"], T[c]["recovery_total_per_healed"])
        rc = ratio(T["P"]["recovery_chan_per_healed"], T[c]["recovery_chan_per_healed"])
        if T[c]["drift_healed"] == 0:
            status = "undefined (no healed drift)"
        elif rt is None or rc is None:              # healed, but at zero extra cost: P cannot be <= 0.25 x 0
            status = "fail (healed drifts cost 0 extra tokens)"
        else:
            status = "pass" if rt <= 0.25 and rc <= 0.25 else "fail"
        r4[c] = {"total_ratio": rt, "chan_ratio": rc, "healed": T[c]["drift_healed"], "status": status}
    r4["pass"] = all(r4[c]["status"] == "pass" for c in "DE")
    preds["R4"] = r4
    trunc, cost = truncation(trans)
    payload = {"model": R["model"], "seeds": sorted({r["seed"] for r in runs}), "scaffold_per_call": sc,
               "ucr_table_tok": A.ntok(A.UCR_TABLE), "tables": tables, "predictions": preds,
               "truncation": {c: {str(f): v for f, v in trunc[c].items()} for c in CONDS},
               "truncation_resend_tok_mean": {c: mean(cost[c]) for c in CONDS}}
    path, dig = save("a3_head_to_head", payload)
    show = {n: {c: {k: v for k, v in t[c].items() if k != "final_errors"} for c in t} for n, t in tables.items()}
    print(json.dumps({"tables": show, "predictions": preds, "truncation": payload["truncation"],
                      "truncation_resend": payload["truncation_resend_tok_mean"]}, indent=1, default=str))
    print(path, dig)


if __name__ == "__main__":
    main()
