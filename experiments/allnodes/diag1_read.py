import json, glob, numpy as np, collections
ORG6 = {}
for f in glob.glob("org6/eval_*.json"):
    for r in json.load(open(f)):
        if "seed" in r: ORG6[r["shade"]] = r["structs"]["own"]
rows = []
for f in sorted(glob.glob("diag/v*.json"), key=lambda x: int(x.split("v")[-1][:-5])):
    d = json.load(open(f)); v = d["shade"]; R = d["rows"]; own = ORG6.get(v)
    bar = lambda r: max([x["G"] for x in r["nat"].values()] + [r["B"]["G"]])
    setter = collections.Counter(max(list(r["nat"].items()) + [("beam-only", r["B"])], key=lambda kv: kv[1]["G"])[0] for r in R)
    un = lambda r: r["nat"]["report+popular"]["ch"]
    def score(c):
        wins = sum(r["st"][c]["G"] > bar(r) for r in R); chok = sum(all(a <= b for a, b in zip(r["st"][c]["ch"], un(r))) for r in R)
        gap = np.mean([r["st"][c]["G"] - bar(r) for r in R]); return wins, chok, gap
    allc = list(R[0]["st"])
    full = [c for c in allc if score(c)[0] == len(R) and score(c)[1] == len(R)]
    best = max(allc, key=lambda c: (score(c)[0] + score(c)[1], score(c)[2]))
    w, ch, gap = score(own) if own else (None, None, None)
    badch = collections.Counter(i for r in R for i, (a, b) in enumerate(zip(r["st"][own]["ch"], un(r))) if a > b) if own else {}
    rows.append((v, d["node"][:24], own, f"{w}/{len(R)}", f"{ch}/{len(R)}", round(gap, 4), dict(setter), full[:4], best, score(best)))
for r in rows: print(r)
