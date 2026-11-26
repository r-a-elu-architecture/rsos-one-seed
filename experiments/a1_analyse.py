"""A1 analysis: numbers for P1-P6 from results/a1_runs.json and results/a1_transcripts.jsonl -> results/a1_agents.json."""

import json
import os
import statistics as stt
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a1_agents as A                      # noqa: E402
from common import save, bootstrap_ci      # noqa: E402

FRACS = (0.1, 0.2, 0.3, 0.4, 0.5)


def mean(x):
    return float(stt.mean(x)) if x else None


def scaffold_sub(run, sc):
    tot = 0
    for c in run["per_call"]:
        s = sc[c["role"]] + (sc["schema_extra"] if run["cond"] == "B" and c["role"] in ("worker", "checker") else 0)
        tot += c["in"] + c["cache_w"] + c["cache_r"] + c["out"] - s
    return tot


def recovery(run):
    """Per drift event: channel + billed tokens and seconds spent after the drift entered (retries, heals)."""
    out = []
    for e in run["drift"]:
        st = e["step"]
        if run["cond"] == "P":
            ch = sum(m["tok"] for m in run["per_msg"] if m["step"] == st and m["kind"] == "heal")
            out.append({"caught": e["caught"], "chan": ch, "billed": 0, "sec": e.get("recovery_sec", 0),
                        "resend": e.get("resend_tok")})
        else:
            msgs = [m for m in run["per_msg"] if m["step"] == st]
            rej = [m for m in msgs if m["from"] == "checker" and m["to"] == "worker"]
            ch = sum(m["tok"] for m in msgs if m["attempt"] >= 1) + sum(m["tok"] for m in rej)
            calls = [c for c in run["per_call"] if c["step"] == st and c["attempt"] >= 1]
            out.append({"caught": e["caught"], "chan": ch,
                        "billed": sum(c["in"] + c["cache_w"] + c["cache_r"] + c["out"] for c in calls),
                        "sec": sum(c["sec"] for c in calls), "retries": len({c["attempt"] for c in calls})})
    return out


def truncation(trans):
    """Cut the tail of every recorded worker->checker message; strict decode by the receiver's protocol."""
    res = {}
    for t in trans:
        c = t["cond"]
        r = res.setdefault(c, {f: {"detected": 0, "silent_wrong": 0, "correct": 0} for f in FRACS})
        res.setdefault(c + "_cost", [])
        for m in t["msgs"]:
            if not (m["from"] == "worker" and m["to"] == "checker" and m["kind"] == "msg"):
                continue
            txt = m["text"]
            for f in FRACS:
                cut = txt[:int(len(txt) * (1 - f))]
                if c == "P":
                    rows = cut.split("\n")
                    det = not (rows[-1].startswith("=") and len(rows[-1]) == 9)
                    same = cut == txt
                else:
                    try:
                        a, b = json.loads(cut), json.loads(txt)
                        det, same = False, a == b
                    except Exception:  # noqa: BLE001
                        det, same = True, False
                r[f]["detected" if det else ("correct" if same else "silent_wrong")] += 1
            res[c + "_cost"].append(A.ntok(txt))      # recovery = resend of that message
    return res


def main():
    R = json.load(open(os.path.join(A.ROOT, "results", "a1_runs.json")))
    trans = [json.loads(l) for l in open(A.TRANSCRIPTS)]
    sc = R["scaffold"]
    runs = R["runs"]
    by = {c: [r for r in runs if r["cond"] == c] for c in A.CONDS}
    table = {}
    for c, rs in by.items():
        rec = [x for r in rs for x in recovery(r)]
        table[c] = {
            "tasks": len(rs), "success": sum(r["success"] for r in rs),
            "line_acc_mean": mean([r["line_acc"] for r in rs]),
            "channel_tok_mean": mean([r["channel_tok"] for r in rs]),
            "channel_tok_ci": bootstrap_ci([r["channel_tok"] for r in rs]),
            "channel_bytes_mean": mean([r["channel_bytes"] for r in rs]),
            "billed_tok_mean": mean([r["billed_tok"] for r in rs]),
            "billed_minus_scaffold_mean": mean([scaffold_sub(r, sc) for r in rs]),
            "out_tok_mean": mean([r["out_tok"] for r in rs]),
            "calls_mean": mean([r["n_calls"] for r in rs]), "msgs_mean": mean([r["n_msgs"] for r in rs]),
            "wall_sec_mean": mean([r["wall_sec"] for r in rs]),
            "cost_usd_total": sum(r["cost_usd"] for r in rs),
            "steps_failed": sum(r["steps_failed"] for r in rs),
            "drift_events": sum(len(r["drift"]) for r in rs),
            "drift_caught": sum(e["caught"] for r in rs for e in r["drift"]),
            "drift_silent_in_final": sum(e["silent_in_final"] for r in rs for e in r["drift"]),
            "recovery_chan_mean_caught": mean([x["chan"] for x in rec if x["caught"]]),
            "recovery_billed_mean_caught": mean([x["billed"] for x in rec if x["caught"]]),
            "recovery_sec_mean_caught": mean([x["sec"] for x in rec if x["caught"]]),
            "final_errors": {r["seed"]: r["final_errors"] for r in rs},
        }
        if c == "P":
            table[c]["heal_over_resend"] = mean([x["chan"] / x["resend"] for x in rec if x["resend"]])
            table[c]["filter_decisions"] = [d for r in rs for e in r["drift"] for d in e.get("filter", [])]
    # full-state resend reference (tokens of one full-state message in A)
    full_state = [m["tok"] for r in by["A"] for m in r["per_msg"] if m["from"] == "planner"]
    trunc = truncation(trans)
    T = table
    preds = {
        "P1": {"ratio_P_over_A": T["P"]["channel_tok_mean"] / T["A"]["channel_tok_mean"],
               "success_P": T["P"]["success"], "success_A": T["A"]["success"],
               "pass": T["P"]["channel_tok_mean"] <= 0.5 * T["A"]["channel_tok_mean"]
               and T["P"]["success"] >= T["A"]["success"] - 1},
        "P2": {c: f"{T[c]['drift_caught']}/{T[c]['drift_events']}" for c in A.CONDS} | {
            "pass": T["P"]["drift_caught"] >= 23 and all(T[c]["drift_caught"] < T["P"]["drift_caught"]
                                                          for c in "ABC")},
        "P3": {"heal_over_full_state_resend": T["P"]["heal_over_resend"],
               "pass": T["P"]["heal_over_resend"] <= 0.5},
        "P4": {"ratio": T["P"]["billed_minus_scaffold_mean"] / T["A"]["billed_minus_scaffold_mean"],
               "pass": T["P"]["billed_minus_scaffold_mean"] <= 0.8 * T["A"]["billed_minus_scaffold_mean"]},
        "P5": {"P": T["P"]["wall_sec_mean"], "A": T["A"]["wall_sec_mean"],
               "pass": T["P"]["wall_sec_mean"] <= T["A"]["wall_sec_mean"]},
    }
    p_det = sum(trunc["P"][f]["detected"] for f in FRACS)
    p_all = sum(sum(trunc["P"][f].values()) for f in FRACS)
    preds["P6"] = {"P_detected": f"{p_det}/{p_all}",
                   "recovery_ratio_P_over_A": mean(trunc["P_cost"]) / mean(trunc["A_cost"]),
                   "pass": p_det == p_all and mean(trunc["P_cost"]) <= 0.5 * mean(trunc["A_cost"])}
    payload = {"model": R["model"], "seeds": A.SEEDS, "scaffold_per_call": sc, "table": table,
               "full_state_msg_tok_mean": mean(full_state), "truncation": {
                   c: {str(f): v for f, v in trunc[c].items()} for c in A.CONDS},
               "truncation_resend_tok_mean": {c: mean(trunc[c + "_cost"]) for c in A.CONDS},
               "predictions": preds}
    path, dig = save("a1_agents", payload)
    print(json.dumps({"table": {c: {k: v for k, v in T[c].items() if k not in ("final_errors", "filter_decisions")}
                                for c in T}, "predictions": preds,
                      "truncation": payload["truncation"]}, indent=1, default=str))
    print(path, dig)


if __name__ == "__main__":
    main()
