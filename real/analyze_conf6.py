"""CONF6 sealed analysis (fixed in real/PREREG_CONF6.md before any CONF6 cell runs). Reads real/outc6/*.json, writes
real/RESULTS_CONF6.md and .json. Nothing here may change after the run.
Primary family (Holm over 2): the WHOLE-system RSOS arm vs PLAIN ROLLOUT, paired by cell, one-sided paired t:
  H1 accuracy gain (whole.result - rollout.result);   H2 tokens saved (rollout.resource - whole.resource).
Law 0, no harm: whole's result vs the standard's: mean >= 0 or 95 % lower bound >= -2 % of the standard's mean result.
LEVEL: UNPRECEDENTED = H1 and H2 both Holm p < 1e-5 and Law 0 holds; STRONG = one of them with Law 0; NOT SHOWN = otherwise.
Reported, decides nothing: whole vs v1 (what binding the whole system adds over RSOS on A only), whole vs noholo
(the hologram's share), all arms vs the standard, wins."""
import os, json, glob, math
from statistics import mean, stdev
from scipy.stats import t as tdist
HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = ("default", "rollout", "v1", "whole", "noholo")

def p_one(x):
    m, s = mean(x), stdev(x)
    if s == 0: return 0.0 if m > 0 else 1.0
    return float(tdist.sf(m / (s / math.sqrt(len(x))), len(x) - 1))

def lo95(x): return mean(x) - tdist.ppf(0.975, len(x) - 1) * stdev(x) / math.sqrt(len(x))

def contrast(C, a, b):
    acc = [c[a]["result"] - c[b]["result"] for c in C]; tok = [c[b]["resource"] - c[a]["resource"] for c in C]
    return {"acc_gain": mean(acc), "p_acc": p_one(acc), "acc_better": sum(x > 0 for x in acc), "acc_worse": sum(x < 0 for x in acc),
            "tokens_saved": mean(tok), "pct_tokens_saved": 100 * mean(tok) / mean(c[b]["resource"] for c in C), "p_tok": p_one(tok),
            "tok_lower": sum(x > 0 for x in tok)}

def main():
    C = [r for f in sorted(glob.glob(os.path.join(HERE, "outc6", "*.json"))) for r in json.load(open(f))["cells"].values() if all(a in r for a in ARMS)]
    P = contrast(C, "whole", "rollout")
    ps = sorted([(P["p_acc"], "acc"), (P["p_tok"], "tok")]); adj = {}; run = 0.0
    for i, (p, k) in enumerate(ps): run = max(run, min(1.0, (2 - i) * p)); adj[k] = run
    h = [c["whole"]["result"] - c["default"]["result"] for c in C]; bs = mean(c["default"]["result"] for c in C)
    law0 = bool(mean(h) >= 0 or lo95(h) >= -0.02 * abs(bs))
    passed = [k for k in ("acc", "tok") if adj[k] < 1e-5]
    level = "UNPRECEDENTED" if len(passed) == 2 and law0 else "STRONG" if passed and law0 else "NOT SHOWN"
    means = {a: {"accuracy": mean(c[a]["result"] for c in C), "tokens": mean(c[a]["resource"] for c in C)} for a in ARMS}
    sec = {f"whole_vs_{b}": contrast(C, "whole", b) for b in ("v1", "noholo", "default")}
    sec["v1_vs_rollout"] = contrast(C, "v1", "rollout")
    json.dump({"level": level, "cells": len(C), "primary": P, "holm": adj, "law0": law0, "means": means, "secondary": sec},
              open(os.path.join(HERE, "RESULTS_CONF6.json"), "w"), indent=1, default=float)
    L = ["# RESULTS CONF6 (sealed; analyze_conf6.py exactly as PREREG_CONF6.md)", "",
         f"**LEVEL: {level}** (AI-AI, {len(C)} fresh cells: whole-system RSOS vs plain rollout on accuracy and tokens, Holm over 2, Law 0).", "",
         "| Contrast | Accuracy gain | Better / worse cells | Holm p (acc) | Tokens saved | Lower-token cells | Holm p (tokens) |", "|---|---|---|---|---|---|---|",
         f"| **whole vs plain rollout** | {P['acc_gain']:+.3f} | {P['acc_better']} / {P['acc_worse']} | {adj['acc']:.1e} | {P['pct_tokens_saved']:+.1f} % | {P['tok_lower']}/{len(C)} | {adj['tok']:.1e} |",
         "", f"Law 0 (no harm vs the standard): {'held' if law0 else 'FAILED'}.", "", "Means per arm (accuracy, tokens):", ""]
    L += [f"- {a}: {m['accuracy']:.3f}, {m['tokens']:.0f}" for a, m in means.items()]
    L += ["", "Secondary (decides nothing; unadjusted one-sided p):", "", "| Contrast | Accuracy gain (p) | Tokens saved (p) |", "|---|---|---|"]
    L += [f"| {k} | {v['acc_gain']:+.3f} ({v['p_acc']:.1e}) | {v['pct_tokens_saved']:+.1f} % ({v['p_tok']:.1e}) |" for k, v in sec.items()]
    open(os.path.join(HERE, "RESULTS_CONF6.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))

if __name__ == "__main__":
    main()
