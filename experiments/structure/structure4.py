"""STRUCTURE4 (owner OK 24 Nov 11:41 to IDENT_STRUCTURE4.md). Layer 2, development quick test, no colour. Sealed and
pushed before the run. LE with relations (STRUCTURE2) + the HOST branch (CLAUDE.md s1: the host decides how a bundle
behaves): for the window starting at t0, every up unit's tendency q_i[landed, neighbour drifted] (learned in replay 1) is
multiplied by the host level h(t0) = (onsets of the channel in replay 2 over ticks < t0 + 1) / (onsets in replay 1 over
ticks < t0 + 1) (+1 smoothing: only ticks before the window, a prediction), capped at 1. Comparison, windows 2/4/8 and
tolerance unchanged. Replays 60 ticks, shades 4 and 10, seed 6670, the sealed structure (run_struct).
Usage: python structure4.py rep <v> <1|2> ; python structure4.py final"""
import os, sys, json
os.environ["S1_T"] = "30"
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import structure2 as S2
S1, L, L4, G, O = S2.S1, S2.L, S2.L4, S2.G, S2.O

def rep(v, r):
    O.T = 60; p = G.params(G.SH["shades"][v - 1]["node"], v); st = L4.st_of(v)
    S1.LAND.clear(); S1.run_struct(L4.replay_class(r), 6670, p, st); tr = L.take()
    json.dump({k: [t[k] for t in tr] for k in ("dry", "dr", "nbd")} | {"land": [[[int(x) for x in s] for s in l] for l in S1.LAND]},
              open(f"diag/S4_v{v}_rep{r}.json", "w"))

def onsets_before(F, t0):
    return sum(int(F[t, i] and not F[t - 1, i]) for t in range(1, t0 + 1) for i in range(F.shape[1]))

def final():
    rows = []
    for v in (4, 10):
        R = {r: json.load(open(f"diag/S4_v{v}_rep{r}.json")) for r in (1, 2)}
        for ch, side in (("dry", 0), ("dr", 1)):
            F0, F1 = np.array(R[1][ch], bool), np.array(R[2][ch], bool)
            if F0.mean() < 0.01 or F1.mean() < 0.01: continue
            N0, N1 = np.array(R[1]["nbd"]) > 0, np.array(R[2]["nbd"]) > 0; A0, A1 = np.zeros_like(F0), np.zeros_like(F1)
            for t, l in enumerate(R[1]["land"]): A0[t, l[side]] = True
            for t, l in enumerate(R[2]["land"]): A1[t, l[side]] = True
            d = {}
            for T in (2, 4, 8):
                preds = []
                for i in range(F0.shape[1]):
                    ups = [t for t in range(F0.shape[0] - T + 1) if not F0[t, i]]; y = {t: F0[t + 1:t + T, i].any() for t in ups}
                    qa = np.mean(list(y.values())) if ups else 0.0; q = {}
                    for l_ in (0, 1):
                        for n_ in (0, 1):
                            z = [y[t] for t in ups if A0[t, i] == l_ and N0[t, i] == n_]; q[(l_, n_)] = np.mean(z) if z else qa
                    for k in range(F1.shape[0] // T):
                        t0 = k * T; h = (onsets_before(F1, t0) + 1) / (onsets_before(F0, t0) + 1)
                        preds.append(1.0 if F1[t0, i] else min(1.0, q[(int(A1[t0, i]), int(N1[t0, i]))] * h))
                pr = float(np.mean(preds)); m = L.span(F1, T); n = F1.shape[1] * (F1.shape[0] // T)
                tol = 2 * np.sqrt(max(pr * (1 - pr), 1e-12) / n) + 0.01; d[T] = {"pred": pr, "meas": m, "tol": float(tol), "ok": bool(abs(m - pr) <= tol)}
            rows.append({"v": v, "ch": ch, "detail": d, "ok": all(x["ok"] for x in d.values())})
    R3 = json.load(open("diag/RESULT_STRUCTURE3.json")); C = dict(R3["checks"]); C["LE_relations"] = all(r["ok"] for r in rows) and len(rows) > 0
    S = {"checks": C, "TABLE_FILLED": all(C.values()), "LE_host": rows, "carried": [k for k in C if k != "LE_relations"]}
    json.dump(S, open("diag/RESULT_STRUCTURE4.json", "w"), default=float, indent=1)
    for r in rows: print(r["v"], r["ch"], r["ok"], {T: (round(x["pred"], 3), round(x["meas"], 3), round(x["tol"], 3)) for T, x in r["detail"].items()})
    print("checks passed", sum(C.values()), "/", len(C), "TABLE_FILLED", S["TABLE_FILLED"])

if __name__ == "__main__":
    rep(int(sys.argv[2]), int(sys.argv[3])) if sys.argv[1] == "rep" else final()
