"""ORG6 analysis: analyze_final.py measures unchanged; files org6/eval_*.json; no births or real data in ORG6."""
import json, glob, numpy as np
from scipy.stats import binomtest
def sp(x):
    x = np.asarray(x, float); w = int((x > 0).sum()); t = int((x != 0).sum())
    return {"wins": w, "nonzero": t, "of": len(x), "mean": float(x.mean()) if len(x) else 0.0, "p": float(binomtest(w, t, 0.5, alternative="greater").pvalue) if t else 1.0}
def holm(ps):
    o = sorted(range(len(ps)), key=lambda i: ps[i]); out = [0] * len(ps); run = 0
    for j, i in enumerate(o): run = max(run, min(1, (len(ps) - j) * ps[i])); out[i] = run
    return out
E = sum([json.load(open(f)) for f in sorted(glob.glob("org6/eval_*.json"))], [])
rows = [r for r in E if "seed" in r]; wrows = [r for r in E if "worlds" in r]
bn = lambda r: max(v["G"] for v in r["nat"].values()); un = lambda r: r["nat"]["report+popular"]; bar = lambda r: max(bn(r), r["B"]["G"])
CTRL = sp([r["own"]["G"] - r["rnd_own"]["G"] for r in rows]); P14 = sp([r["nb"]["G"] - r["rnd_nb"]["G"] for r in rows])
CB = sp([r["nb"]["G"] - r["glob"]["G"] for r in rows])
W = {wn: sp([x["worlds"][wn]["nb"] - max(x["worlds"][wn]["nat"].values()) for x in wrows]) for wn in ("WB", "WC")}
shades = sorted({r["shade"] for r in rows}); S = {}
for v in shades:
    a = sorted([r for r in rows if r["shade"] == v], key=lambda r: r["seed"])
    S[v] = {"node": a[0]["node"], "structs": a[0]["structs"], "P0": sp([r["own"]["G"] - un(r)["G"] for r in a]),
            "P5": sp([r["own"]["G"] - bar(r) for r in a]), "channels_ok": sum(all(x <= y for x, y in zip(r["own"]["ch"], un(r)["ch"])) for r in a),
            "repeat": [sum(r["own"]["G"] > bar(r) for r in a[:6]), sum(r["own"]["G"] > bar(r) for r in a[6:])],
            "transfer": sp([r["nb"]["G"] - r["rnd_nb"]["G"] for r in a])}
h0 = holm([S[v]["P0"]["p"] for v in shades]); h5 = holm([S[v]["P5"]["p"] for v in shades])
for i, v in enumerate(shades):
    s = S[v]; s["holm_P0"], s["holm_P5"] = h0[i], h5[i]
    s["m"] = {"control": CTRL["p"] < 0.05, "m1": h0[i] < 0.05, "m2": s["channels_ok"] >= 10, "m3": h5[i] < 0.05,
              "m4": CTRL["p"] < 0.05 and P14["p"] < 0.05, "m5": min(s["repeat"]) >= 4, "m6": W["WB"]["p"] < 0.05 and W["WC"]["p"] < 0.05}
    s["green"] = all(s["m"].values())
pf = lambda r, k: (r[k]["G"] - un(r)["G"]) / max(1, r[k]["flows"])
P8b = sp([pf(r, "own") - pf(r, "all") for r in rows])
out = {"shades": S, "n_green": sum(S[v]["green"] for v in shades), "control": CTRL, "P14_transfer_A": P14, "claim_B_nb_vs_glob": CB,
       "worlds": W, "P8b": P8b}
json.dump(out, open("RESULTS_ORG6.json", "w"), indent=1)
for v in shades:
    s = S[v]; print(f"v{v:2d} {s['node'][:22]:22s} own {s['structs']['own']} nb {s['structs']['nb']} P0 {s['P0']['wins']}/{s['P0']['nonzero']} P5 {s['P5']['wins']}/{s['P5']['nonzero']} holm5 {s['holm_P5']:.4f} ch {s['channels_ok']}/12 rep {s['repeat']} tr {s['transfer']['wins']}/{s['transfer']['nonzero']} {'GREEN' if s['green'] else '-'} {[k for k, x in s['m'].items() if not x]}")
print(json.dumps({k: out[k] for k in out if k != "shades"}, indent=1, default=str))
