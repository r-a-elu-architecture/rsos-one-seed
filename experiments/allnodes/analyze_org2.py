"""ORG2 analysis exactly as PREREG_ORG2.md (ORG1 rules + P14', P4b' >= 8 corrupted, P16' births, P5t)."""
import json, glob, numpy as np
from scipy.stats import binomtest
def sp(x):
    x = np.asarray(x, float); w = int((x > 0).sum()); t = int((x != 0).sum())
    return {"wins": w, "nonzero": t, "of": len(x), "mean": float(x.mean()), "p": float(binomtest(w, t, 0.5, alternative="greater").pvalue) if t else 1.0}
def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); out = [0] * len(ps); run = 0
    for j, i in enumerate(o): run = max(run, min(1, (len(ps) - j) * ps[i])); out[i] = run
    return out
r1 = sum([json.load(open(f)) for f in sorted(glob.glob("RAW2_round1_w*.json"))], [])
r2d = [json.load(open(f)) for f in sorted(glob.glob("RAW2_round2_w*.json"))]; r2 = sum([d["rows"] for d in r2d], [])
proto = r2d[0]["protocol"]
bn = lambda r: max(v["G"] for v in r["nat"].values()); un = lambda r: r["nat"]["report+popular"]
shades = sorted({r["shade"] for r in r1}); S = {}
lim = [r["lim_imprint"]["G"] - r["lim_random"]["G"] for r in r2]; P14 = sp(lim)
for v in shades:
    a = [r for r in r1 if r["shade"] == v]; b = [r for r in r2 if r["shade"] == v]; allr = a + b
    p0 = sp([r["S"]["G"] - un(r)["G"] for r in allr]); p5 = sp([r["S"]["G"] - bn(r) for r in allr])
    ch = sum(all(x <= y for x, y in zip(r["S"]["ch"], un(r)["ch"])) for r in allr)
    rep = [sum(r["S"]["G"] > bn(r) for r in a), sum(r["S"]["G"] > bn(r) for r in b)]
    S[v] = {"node": a[0]["node"], "P0": p0, "P5": p5, "channels_ok": ch, "repeat": rep}
h0 = holm([S[v]["P0"]["p"] for v in shades]); h5 = holm([S[v]["P5"]["p"] for v in shades])
for i, v in enumerate(shades):
    s = S[v]; s["holm_P0"], s["holm_P5"] = h0[i], h5[i]
    s["m"] = {"m1": h0[i] < 0.05, "m2": s["channels_ok"] >= 10, "m3": h5[i] < 0.05, "m4": P14["p"] < 0.05, "m5": min(s["repeat"]) >= 4}
    s["green"] = all(s["m"].values())
fails_r1 = sum(1 for v in shades if sum(r["S"]["G"] > bn(r) for r in r1 if r["shade"] == v) < 4)
pf = lambda r, k: (r[k]["G"] - un(r)["G"]) / max(1, r[k]["flows"])
P8b = sp([pf(r, "S") - pf(r, "all") for r in r1 + r2])
ch = sum([json.load(open(f)) for f in sorted(glob.glob("RAW2_births_w*.json"))], [])
P16 = sp([r["child"]["G"] - max(r["parentA_cfg"]["G"], r["parentB_cfg"]["G"]) for r in ch if r["differs"]])
P4b = {**proto, "pass": proto["corrupted_adopted"] == 0 and proto["rejected_hash"] == proto["corrupted_total"] and proto["corrupted_total"] >= 8}
real = json.load(open("RAW2_real.json"))
RE = {"P5t": sp([r["temporal"] - r["best_native"] for r in real]), "P5t_vs_decay": sp([r["temporal"] - r["decay"] for r in real])}
RE["by_data"] = {n: sp([r["temporal"] - r["best_native"] for r in real if r["data"] == n]) for n in ("cancer", "wine", "digits")}
out = {"shades": S, "n_green": sum(S[v]["green"] for v in shades), "P14": P14, "P15": "not measurable (no fever)" if fails_r1 < 3 else fails_r1,
       "P8b": P8b, "P16": P16, "P4b": P4b, "real": RE}
json.dump(out, open("RESULTS_ORG2.json", "w"), indent=1)
for v in shades:
    s = S[v]; print(f"v{v:2d} {s['node'][:22]:22s} P0 {s['P0']['wins']}/{s['P0']['nonzero']} P5 {s['P5']['wins']}/{s['P5']['nonzero']} holm5 {s['holm_P5']:.4f} ch {s['channels_ok']}/12 rep {s['repeat']} {'GREEN' if s['green'] else '-'} {[k for k, x in s['m'].items() if not x]}")
print(json.dumps({k: out[k] for k in ("n_green", "P14", "P15", "P8b", "P16", "P4b", "real")}, indent=1))
