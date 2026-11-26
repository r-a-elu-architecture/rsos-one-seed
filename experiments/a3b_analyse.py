"""A3b analysis: B1-B7 (PREREGISTRATION_A3B.md) -> results/a3b_hologram.json.

1. Re-use check for A3's P and D (and E for B7): a1_agents.py unchanged since 8408a00, and every recorded A3 P/D/E
   run replayed through the current harness reproduces its A3 result record.
2. BPE recount of P, D, E from the A3 transcripts (guard against regex-proxy artefacts).
3. H arms from results/a3b_runs.json + results/a3b_transcripts.jsonl; offline truncation with full decode + hash.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a1_agents as A                      # noqa: E402
import a3_run                              # noqa: E402
import a3b_hologram as H                   # noqa: E402
from a1_analyse import FRACS, mean, scaffold_sub   # noqa: E402
from a3_analyse import summarise as a3_summarise   # noqa: E402
from common import bootstrap_ci, save      # noqa: E402

if H._BPE is None:  # without o200k every BPE count is -1, and B1/B2/B5 silently flip
    sys.exit("a3b_analyse: tiktoken (o200k_base) is required; install it before re-running the analysis")

R = A.ROOT
EDGE = {("planner", "worker"): "instruction", ("worker", "checker"): "edits", ("checker", "worker"): "door",
        ("checker", "planner"): "forward"}
CHECK = ("success", "line_acc", "replica_success", "final_errors", "steps_failed", "n_calls", "channel_tok",
         "channel_bytes", "billed_tok", "out_tok")


def edge_of(m):
    return "heal" if m["kind"] == "heal" else EDGE.get((m["from"], m["to"]), "other")


def reuse_check():
    diff = subprocess.run(["git", "-C", R, "diff", "8408a00", "--", "experiments/a1_agents.py"],
                          capture_output=True, text=True).stdout
    rec = {(r["cond"], r["seed"]): r for r in json.load(open(os.path.join(R, "results", "a3_runs.json")))["runs"]}
    os.environ["A_TRANSCRIPTS"] = os.devnull
    n, bad = 0, []
    for line in open(os.path.join(R, "results", "a3_transcripts.jsonl")):
        t = json.loads(line)
        if t["cond"] not in "PDE":
            continue
        r = a3_run.replay(t)
        o = rec[(t["cond"], t["seed"])]
        n += 1
        for k in CHECK:
            if r[k] != o[k]:
                bad.append((t["cond"], t["seed"], k))
        if [{k: e[k] for k in ("key", "healed", "healed_zero_call")} for e in r["drift"]] != \
                [{k: e[k] for k in ("key", "healed", "healed_zero_call")} for e in o["drift"]]:
            bad.append((t["cond"], t["seed"], "drift"))
    del os.environ["A_TRANSCRIPTS"]
    return {"a1_agents_diff_empty": diff == "", "replayed": n, "mismatches": bad,
            "pass": diff == "" and not bad}


def a3_bpe():
    out = {}
    for line in open(os.path.join(R, "results", "a3_transcripts.jsonl")):
        t = json.loads(line)
        d = out.setdefault(t["cond"], {"tok": [], "bpe": [], "bytes": [], "edges": {}})
        d["tok"].append(sum(m["tok"] for m in t["msgs"]))
        d["bpe"].append(sum(H.bpe(m["text"]) for m in t["msgs"]))
        d["bytes"].append(sum(m["bytes"] for m in t["msgs"]))
        for m in t["msgs"]:
            e = d["edges"].setdefault(edge_of(m), [0, 0])
            e[0] += m["tok"]; e[1] += H.bpe(m["text"])
    return {c: {"tok_mean": mean(d["tok"]), "bpe_mean": mean(d["bpe"]), "bytes_mean": mean(d["bytes"]),
                "edges_tok_bpe_per_task": {k: [v[0] / len(d["tok"]), v[1] / len(d["tok"])] for k, v in d["edges"].items()}}
            for c, d in out.items()}


def h_summary(rs, sc):
    ev = [e for r in rs for e in r["drift"]]
    heal = []
    for r in rs:
        for e in r["drift"]:
            if e["healed"]:
                heal.append(sum(m["tok"] for m in r["per_msg"] if m["step"] == e["step"] and m["kind"] == "heal"))
    edges = {}
    for r in rs:
        for m in r["per_msg"]:
            x = edges.setdefault(edge_of(m), [0, 0]); x[0] += m["tok"]; x[1] += m["bpe"]
    return {
        "tasks": len(rs), "success": sum(r["success"] for r in rs),
        "replica_success": sum(r["replica_success"] for r in rs),
        "wrong_final_lines": sum(len(r["final_errors"]) for r in rs),
        "channel_tok_mean": mean([r["channel_tok"] for r in rs]),
        "channel_tok_ci": bootstrap_ci([r["channel_tok"] for r in rs]),
        "channel_bpe_mean": mean([r["channel_bpe"] for r in rs]),
        "channel_bytes_mean": mean([r["channel_bytes"] for r in rs]),
        "edges_tok_bpe_per_task": {k: [v[0] / len(rs), v[1] / len(rs)] for k, v in edges.items()},
        "billed_tok_mean": mean([r["billed_tok"] for r in rs]),
        "billed_minus_scaffold_mean": mean([scaffold_sub(r, sc) for r in rs]),
        "calls_mean": mean([r["n_calls"] for r in rs]), "wall_sec_mean": mean([r["wall_sec"] for r in rs]),
        "cost_usd_total": sum(r["cost_usd"] for r in rs), "steps_failed": sum(r["steps_failed"] for r in rs),
        "drift_events": len(ev), "drift_healed": sum(e["healed"] for e in ev),
        "drift_healed_zero_call": sum(e["healed_zero_call"] for e in ev),
        "drift_in_authoritative_final": sum(e["silent_in_final"] for e in ev),
        "drift_in_any_copy_final": sum(e["in_any_copy_final"] for e in ev),
        "recovery_chan_per_healed": mean(heal) if heal else None,
        "fallback_heal_tok_mean": mean([e["fallback_heal_tok"] for e in ev if "fallback_heal_tok" in e]),
        "final_errors": {r["seed"]: r["final_errors"] for r in rs},
    }


def truncation(cond, trans):
    codec = H.codec_of(cond)
    res = {f: {"detected": 0, "silent_wrong": 0, "correct": 0} for f in FRACS}
    for t in trans:
        if t["cond"] != cond:
            continue
        codec.new_task(A.text_of(A.make_task(t["seed"])["init"]))
        for m in t["msgs"]:
            if not (m["from"] == "worker" and m["to"] == "checker" and m["kind"] == "msg"):
                continue
            try:
                full = codec.dec_edits(m["text"], m["book"])
            except H.Undecodable:
                full = None            # sender/receiver mismatch in the live run (healed then); compare to None
            for f in FRACS:
                cut = m["text"][:int(len(m["text"]) * (1 - f))]
                try:
                    got = codec.dec_edits(cut, m["book"])
                except Exception:  # noqa: BLE001
                    res[f]["detected"] += 1; continue
                res[f]["correct" if (cut == m["text"] or got == full) else "silent_wrong"] += 1
    return res


def mechanism_stats(trans):
    """H-dragon: forward hits/misses, literal share of the instruction, dictionary reuse, fallbacks."""
    import re
    out = {}
    for c in ("Hc", "Hd"):
        ts = [t for t in trans if t["cond"] == c]
        if not ts:
            continue
        ins = [m for t in ts for m in t["msgs"] if m["from"] == "planner" and m["to"] == "worker"]
        fwd = [m for t in ts for m in t["msgs"] if m["from"] == "checker" and m["to"] == "planner"]
        miss = sum(1 for t in ts for m in t["msgs"] if m["from"] == "planner" and m["to"] == "checker"
                   and m["text"] == "?")
        lit_tok = sum(A.ntok("".join(re.findall(r"«((?:[^»]|»»)*)»", m["text"]))) for m in ins)
        out[c] = {"instructions": len(ins), "instr_tok": sum(m["tok"] for m in ins),
                  "instr_literal_content_tok": lit_tok,
                  "instr_all_literal": sum(1 for m in ins if re.fullmatch(r"«(?:[^»]|»»)*»", m["text"])),
                  "instr_with_D_ref": sum(1 for m in ins if re.search(r"(^| )D\d+( |$)", m["text"])),
                  "approvals": sum(1 for m in fwd if re.fullmatch(r"\d{6}", m["text"])),
                  "forward_miss": miss,
                  "edits_fallback": sum(1 for t in ts for m in t["msgs"] if m["from"] == "worker"
                                        and m["to"] == "checker" and m["text"].startswith("~")),
                  "heal_msgs": sum(1 for t in ts for m in t["msgs"] if m["kind"] == "heal")}
    return out


def main():
    reuse = reuse_check()
    print("reuse", reuse, flush=True)
    a3 = json.load(open(os.path.join(R, "results", "a3_runs.json")))
    sc = a3["scaffold"]
    A3T = {c: a3_summarise([r for r in a3["runs"] if r["cond"] == c], sc) for c in "PADE"}
    bpe3 = a3_bpe()
    runs, trans = [], []
    for f in ("a3b_results.jsonl", "a3b_results_hd.jsonl"):
        fp = os.path.join(R, "results", f)
        if os.path.exists(fp):
            runs += [json.loads(l) for l in open(fp)]
    for f in ("a3b_transcripts.jsonl", "a3b_transcripts_hd.jsonl"):
        fp = os.path.join(R, "results", f)
        if os.path.exists(fp):
            trans += [json.loads(l) for l in open(fp)]
    runs = sorted({(r["cond"], r["seed"]): r for r in runs}.values(), key=lambda r: (r["seed"], r["cond"]))
    json.dump({"model": A.MODEL, "runs": runs}, open(os.path.join(R, "results", "a3b_runs.json"), "w"), indent=1)
    conds = [c for c in ("Hc", "Hd") if any(r["cond"] == c for r in runs)]
    T = {c: h_summary([r for r in runs if r["cond"] == c], sc) for c in conds}
    trunc = {c: truncation(c, trans) for c in conds}
    design = json.load(open(os.path.join(R, "results", "a3b_dragon_design.json")))["design"]
    D_tok, D_bpe, E_rec = A3T["D"]["channel_tok_mean"], bpe3["D"]["bpe_mean"], A3T["E"]["recovery_chan_per_healed"]
    preds = {}
    for c in conds:
        t = T[c]
        silent = sum(v["silent_wrong"] for v in trunc[c].values())
        b1 = t["channel_tok_mean"] <= D_tok
        b2 = t["channel_tok_mean"] <= 0.2 * D_tok
        preds[c] = {
            "B1": {"H": t["channel_tok_mean"], "D": D_tok, "ratio": t["channel_tok_mean"] / D_tok,
                   "bpe_H": t["channel_bpe_mean"], "bpe_D": D_bpe, "bpe_ratio": t["channel_bpe_mean"] / D_bpe,
                   "pass": b1 and t["channel_bpe_mean"] <= D_bpe,
                   "proxy_artefact": b1 and t["channel_bpe_mean"] > D_bpe},
            "B2": {"limit": 0.2 * D_tok, "pass": b2 and t["channel_bpe_mean"] <= 0.2 * D_bpe,
                   "proxy_artefact": b2 and t["channel_bpe_mean"] > 0.2 * D_bpe},
            "B3": {"healed_zero_call": f"{t['drift_healed_zero_call']}/{t['drift_events']}",
                   "replica_consistent": f"{t['replica_success']}/{t['tasks']}", "truncation_silent": silent,
                   "pass": t["drift_healed_zero_call"] == t["drift_events"] == 48 and t["replica_success"] == 16
                   and silent == 0},
            "B4": {"H": t["success"], "D": A3T["D"]["success"], "pass": t["success"] >= A3T["D"]["success"]},
            "B7": {"H_per_healed": t["recovery_chan_per_healed"], "E": E_rec, "limit": 0.25 * E_rec,
                   "pass": t["recovery_chan_per_healed"] is not None and t["recovery_chan_per_healed"] <= 0.25 * E_rec},
        }
    if "Hd" in T and "Hc" in T:
        b5 = T["Hd"]["channel_tok_mean"] <= T["Hc"]["channel_tok_mean"]
        preds["B5"] = {"Hd": T["Hd"]["channel_tok_mean"], "Hc": T["Hc"]["channel_tok_mean"],
                       "bpe_Hd": T["Hd"]["channel_bpe_mean"], "bpe_Hc": T["Hc"]["channel_bpe_mean"],
                       "pass": b5 and T["Hd"]["channel_bpe_mean"] <= T["Hc"]["channel_bpe_mean"]
                       and preds["Hd"]["B3"]["pass"],
                       "proxy_artefact": b5 and T["Hd"]["channel_bpe_mean"] > T["Hc"]["channel_bpe_mean"]}
    if "Hd" in T:
        pr = design["predicted_channel_tok_per_task"]
        preds["B6"] = {"predicted": pr, "measured": T["Hd"]["channel_tok_mean"],
                       "rel_err": (pr - T["Hd"]["channel_tok_mean"]) / T["Hd"]["channel_tok_mean"],
                       "pass": abs(pr - T["Hd"]["channel_tok_mean"]) <= 0.5 * T["Hd"]["channel_tok_mean"]}
    mech = mechanism_stats(trans)
    payload = {"mechanism_stats": mech, "model": A.MODEL, "seeds": H.SEEDS, "reuse_check": reuse, "a3_bpe": bpe3,
               "a3_tables": {c: {k: v for k, v in A3T[c].items() if k != "final_errors"} for c in "PADE"},
               "tables": T, "truncation": {c: {str(f): v for f, v in trunc[c].items()} for c in conds},
               "predictions": preds, "dragon_predicted": {k: design[k] for k in design if k.startswith("predicted")}}
    path, dig = save("a3b_hologram", payload)
    print(json.dumps({"tables": {c: {k: v for k, v in T[c].items() if k != "final_errors"} for c in T},
                      "predictions": preds, "truncation": payload["truncation"], "a3_bpe": bpe3}, indent=1,
                     default=str))
    print(path, dig)


if __name__ == "__main__":
    main()
