"""DIAG1 (exploratory diagnosis, development seeds 7000-7003, never used for colours; owner 22 Nov 17:11 "start").
For each of the 14 shades not green under ORG6: who sets the bar (strongest native or beam-only), how far the ORG6 pick
is from it, whether ANY of the 16 existing structures clears the bar and keeps the channels (then the failure is
selection), or none does (then a structure is missing), and which channel is the one that gets worse.
Usage: python diag1.py <part 0|1>"""
import sys, os, json, hashlib
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import org5 as Z
G, O, F4, run_st, unkey, key, STRUCTS = Z.G, Z.O, Z.F4, Z.run_st, Z.unkey, Z.key, Z.STRUCTS
SEEDS = [7000, 7001, 7002, 7003]
NONGREEN = [3, 5, 7, 9, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21]
part = int(sys.argv[1])
for v in [x for i, x in enumerate(NONGREEN) if i % 2 == part]:
    f = f"diag/v{v}.json"
    if os.path.exists(f): continue
    k = v - 1; p = G.params(G.SH["shades"][k]["node"], v); out = []
    for sd in SEEDS:
        nat = {f"{a}+{b}": F4.run(G.Shade, sd, p, (a, b)) for a, b in O.NATS}; B = F4.run(G.Shade, sd, p, "B")
        st = {key(s): run_st(G.Shade, sd, p, s) for s in STRUCTS}
        out.append({"seed": sd, "nat": {a: {"G": r["G"], "ch": r["ch"]} for a, r in nat.items()}, "B": {"G": B["G"], "ch": B["ch"]},
                    "st": {c: {"G": r["G"], "ch": r["ch"]} for c, r in st.items()}})
    json.dump({"shade": v, "node": G.SH["shades"][k]["node"], "params": p, "rows": out}, open(f, "w")); print("diag", v, flush=True)
