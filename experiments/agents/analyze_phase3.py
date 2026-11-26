"""Phase 3 analysis, exactly as PREREG_AGENTS_PHASE3.md (written before any phase 3 call).
Usage: python analyze_phase3.py phase3_staff.jsonl phase3_orders.jsonl  -> prints and writes RESULTS_PHASE3.json
Unit = one (model, task) pair; arms are compared on the same pairs (paired). Errored rows count as wrong."""
import sys, json, collections, random
from scipy.stats import binomtest
T = "rsos_01100"; BASES = ["react", "reflexion", "selfcons", "planexec"]

def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); out = [0] * len(ps); run = 0
    for j, i in enumerate(o): run = max(run, min(1, (len(ps) - j) * ps[i])); out[i] = run
    return out

last = {}
for path in sys.argv[1:]:
    for l in open(path):
        r = json.loads(l); last[(r["model"], r["arm"], r["task"])] = r
by = collections.defaultdict(dict)
for (m, a, t), r in last.items(): by[a][(m, t)] = r
models = sorted({m for m, a, t in last})
units = sorted(set(by[T]).intersection(*[set(by[b]) for b in BASES]))
def sign(a, b, keys):
    w = sum(1 for k in keys if by[a][k]["correct"] and not by[b][k]["correct"]); l = sum(1 for k in keys if by[b][k]["correct"] and not by[a][k]["correct"])
    return {"wins": w, "losses": l, "n": len(keys), "p": float(binomtest(w, w + l, 0.5, alternative="greater").pvalue) if w + l else 1.0}
acc = lambda a, keys: sum(by[a][k]["correct"] for k in keys) / len(keys)
out = {"units": len(units), "models": models, "accuracy": {a: acc(a, units) for a in [T] + BASES},
       "errors": sum(1 for k in units for a in [T] + BASES if by[a][k]["error"])}
# H1 (primary): T > react, pooled
out["H1"] = sign(T, "react", units); out["H1"]["pass"] = out["H1"]["p"] < 0.05
# H2: T > react in each model, Holm over models (tested only if H1 passes)
h2 = {m: sign(T, "react", [k for k in units if k[0] == m]) for m in models}
for m, p in zip(models, holm([h2[m]["p"] for m in models])): h2[m]["holm"] = p; h2[m]["pass"] = out["H1"]["pass"] and p < 0.05
out["H2"] = h2
# H3: T > each of reflexion, selfcons, planexec, pooled, Holm over 3
h3 = {b: sign(T, b, units) for b in BASES[1:]}
for b, p in zip(BASES[1:], holm([h3[b]["p"] for b in BASES[1:]])): h3[b]["holm"] = p; h3[b]["pass"] = p < 0.05
out["H3"] = h3
# H4: cost and non-inferiority vs selfcons: tokens per correct answer ratio T/selfcons, 95% bootstrap CI (10,000 resamples of
# units, seed 4242); pass if CI upper < 0.80 AND accuracy difference T - selfcons has 95% bootstrap CI lower bound > -0.03
rng = random.Random(4242); ratios, diffs = [], []
tok = lambda a, ks: sum((by[a][k]["tokens"] or 0) for k in ks); cor = lambda a, ks: sum(by[a][k]["correct"] for k in ks)
for _ in range(10000):
    ks = [units[rng.randrange(len(units))] for _ in units]
    ratios.append((tok(T, ks) / max(1, cor(T, ks))) / (tok("selfcons", ks) / max(1, cor("selfcons", ks))))
    diffs.append((cor(T, ks) - cor("selfcons", ks)) / len(ks))
ratios.sort(); diffs.sort(); q = lambda v, x: v[int(x * (len(v) - 1))]
r0 = (tok(T, units) / max(1, cor(T, units))) / max(1e-9, tok("selfcons", units) / max(1, cor("selfcons", units)))
out["H4"] = {"tokens_per_correct_ratio": r0, "ratio_ci95": [q(ratios, .025), q(ratios, .975)],
             "acc_diff": acc(T, units) - acc("selfcons", units), "acc_diff_ci95": [q(diffs, .025), q(diffs, .975)]}
out["H4"]["pass"] = out["H4"]["ratio_ci95"][1] < 0.80 and out["H4"]["acc_diff_ci95"][0] > -0.03
out["per_model_accuracy"] = {m: {a: acc(a, [k for k in units if k[0] == m]) for a in [T] + BASES} for m in models}
out["per_family_accuracy"] = {f: {a: acc(a, [k for k in units if by[a][k]["family"] == f]) for a in [T] + BASES} for f in sorted({by[T][k]["family"] for k in units})}
json.dump(out, open("RESULTS_PHASE3.json", "w"), indent=1)
print(json.dumps(out, indent=1))
