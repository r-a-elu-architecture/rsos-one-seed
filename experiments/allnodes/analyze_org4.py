"""ORG4 analysis exactly as PREREG_ORG4.md."""
import json, glob, numpy as np
from scipy.stats import binomtest
def sp(x):
    x = np.asarray(x, float); w = int((x > 0).sum()); t = int((x != 0).sum())
    return {"wins": w, "nonzero": t, "of": len(x), "mean": float(x.mean()) if len(x) else 0.0, "p": float(binomtest(w, t, 0.5, alternative="greater").pvalue) if t else 1.0}
def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); out = [0] * len(ps); run = 0
    for j, i in enumerate(o): run = max(run, min(1, (len(ps) - j) * ps[i])); out[i] = run
    return out
d1 = [json.load(open(f)) for f in sorted(glob.glob("RAW4_round1_w*.json"))]; r1 = sum([d["rows"] for d in d1], []); wo = sum([d["worlds"] for d in d1], [])
d2 = [json.load(open(f)) for f in sorted(glob.glob("RAW4_round2_w*.json"))]; r2 = sum([d["rows"] for d in d2], []); proto = d2[0]["protocol"]
bn = lambda r: max(v["G"] for v in r["nat"].values()); un = lambda r: r["nat"]["report+popular"]; bar = lambda r: max(bn(r), r["B"]["G"])
shades = sorted({r["shade"] for r in r1}); S = {}
P14 = sp([r["lim_library"]["G"] - r["lim_random"]["G"] for r in r2])
SELF = sp([r["lim_self"]["G"] - r["lim_random"]["G"] for r in r2 if r["lim_self"]])
W = {wn: sp([x["S"] - max(x["nat"].values()) for x in wo if x["world"] == wn]) for wn in ("WB", "WC")}
for v in shades:
    a = [r for r in r1 if r["shade"] == v]; b = [r for r in r2 if r["shade"] == v]; allr = a + b
    S[v] = {"node": a[0]["node"], "P0": sp([r["S"]["G"] - un(r)["G"] for r in allr]), "P5": sp([r["S"]["G"] - bar(r) for r in allr]),
            "channels_ok": sum(all(x <= y for x, y in zip(r["S"]["ch"], un(r)["ch"])) for r in allr),
            "repeat": [sum(r["S"]["G"] > bar(r) for r in a), sum(r["S"]["G"] > bar(r) for r in b)],
            "transfer": sp([r["lim_library"]["G"] - r["lim_random"]["G"] for r in b])}
h0 = holm([S[v]["P0"]["p"] for v in shades]); h5 = holm([S[v]["P5"]["p"] for v in shades])
for i, v in enumerate(shades):
    s = S[v]; s["holm_P0"], s["holm_P5"] = h0[i], h5[i]
    s["m"] = {"m1": h0[i] < 0.05, "m2": s["channels_ok"] >= 10, "m3": h5[i] < 0.05, "m4": P14["p"] < 0.05, "m5": min(s["repeat"]) >= 4,
              "m6": W["WB"]["p"] < 0.05 and W["WC"]["p"] < 0.05}
    s["green"] = all(s["m"].values())
fails_r1 = sum(1 for v in shades if sum(r["S"]["G"] > bar(r) for r in r1 if r["shade"] == v) < 4)
pf = lambda r, k: (r[k]["G"] - un(r)["G"]) / max(1, r[k]["flows"])
P8b = sp([pf(r, "S") - pf(r, "all") for r in r1 + r2])
P4b = {**proto, "pass": proto["corrupted_adopted"] == 0 and proto["rejected_hash"] == 9 and proto["corrupted_total"] == 9 and proto["valid_rejected"] == 0}
prec = [r["lim_library"]["precision"] for r in r2 if r["lim_library"]["precision"] is not None]
prec_r = [r["lim_random"]["precision"] for r in r2 if r["lim_random"]["precision"] is not None]
out = {"shades": S, "n_green": sum(S[v]["green"] for v in shades), "P14": P14, "self_control": SELF, "worlds": W,
       "P15": "not measurable (no fever)" if fails_r1 < 3 else fails_r1, "P8b": P8b, "P4b": P4b,
       "precision_library": float(np.mean(prec)), "precision_random": float(np.mean(prec_r)),
       "beam_only_vs_best_native": sp([r["B"]["G"] - bn(r) for r in r1 + r2]), "guard_mean": float(np.mean([r["S"]["guard"] for r in r1 + r2]))}
json.dump(out, open("RESULTS_ORG4.json", "w"), indent=1)
for v in shades:
    s = S[v]; print(f"v{v:2d} {s['node'][:22]:22s} P0 {s['P0']['wins']}/{s['P0']['nonzero']} P5 {s['P5']['wins']}/{s['P5']['nonzero']} holm5 {s['holm_P5']:.4f} ch {s['channels_ok']}/12 rep {s['repeat']} tr {s['transfer']['wins']}/{s['transfer']['nonzero']} {'GREEN' if s['green'] else '-'} {[k for k, x in s['m'].items() if not x]}")
print(json.dumps({k: out[k] for k in out if k != "shades"}, indent=1))
