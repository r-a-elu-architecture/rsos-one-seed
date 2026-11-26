"""Quick loop (development seeds 7000-7001, the DIAG1 seeds; bar and natives read from diag/v*.json, never used for colours).
For each listed shade: its ORG6 own structure plus each new-role combination; reports wins over the bar and channels.
Usage: python quick7.py <part> <combos comma list, e.g. none,cs,vote,mem,joint,all>"""
import sys, json, glob, time
import org7 as X
ORG6 = {}
for f in glob.glob("org6/eval_*.json"):
    for r in json.load(open(f)):
        if "seed" in r: ORG6[r["shade"]] = r["structs"]["own"]
SHADES = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else [3, 5, 7, 9, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21]; SEEDS = [7000, 7001]
part, combos = int(sys.argv[1]), sys.argv[2].split(",")
for v in [x for i, x in enumerate(SHADES) if i % 2 == part]:
    p = X.G.params(X.G.SH["shades"][v - 1]["node"], v)
    try: D = {r["seed"]: r for r in json.load(open(f"diag/v{v}.json"))["rows"]}
    except FileNotFoundError:
        D = {sd: {"nat": {f"{a}+{b}": X.F4.run(X.G.Shade, sd, p, (a, b)) for a, b in X.O.NATS}, "B": X.F4.run(X.G.Shade, sd, p, "B")} for sd in SEEDS}
    base = X.Z.unkey(ORG6[v]); out = {}
    for c in combos:
        parts = c.split("+"); st = dict(base, **{k: int(k in parts or c == "all") for k in X.NEW}); res = []
        if "cs1" in parts: st["cs"], st["cs_th"] = 1, 1
        for sd in SEEDS:
            t0 = time.time(); r = X.run_st2(X.G.Shade, sd, p, st); d = D[sd]
            bar = max([x["G"] for x in d["nat"].values()] + [d["B"]["G"]]); un = d["nat"]["report+popular"]["ch"]
            res.append({"gap": r["G"] - bar, "chok": all(a <= b for a, b in zip(r["ch"], un)), "ch": r["ch"], "un": un, "sec": round(time.time() - t0)})
        out[c] = res; print(v, c, [(round(x["gap"], 4), x["chok"], x["sec"]) for x in res], flush=True)
    json.dump(out, open(f"diag/quick7{sys.argv[4] if len(sys.argv) > 4 else ''}_v{v}.json", "w"))
