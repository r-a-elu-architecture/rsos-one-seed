"""AGENTS2 analysis. Predictions: PREREG_AGENTS2.md (sealed first)."""
import glob
import json
import math
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PUB = os.environ.get("RSOS_LANGUAGE", "/home/claude/rsos-language")


def main():
    cnt = {arm: defaultdict(lambda: [0, 0]) for arm in ("JP", "X5b")}
    strata = defaultdict(lambda: [[0, 0], [0, 0]])          # kind -> [first quartile [err, n], last quartile [err, n]]
    files = sorted(glob.glob(os.path.join(PUB, "results", "a7_results_*.jsonl")))
    for f in files:
        for line in open(f):
            r = json.loads(line)
            arm = "JP" if r["arm"] in ("B2", "B2s") else ("X5b" if r["arm"] == "X5b" else None)
            steps = r.get("steps") or []
            if not arm or not steps:
                continue
            L = len(steps)
            for s in steps:
                if "correct" not in s:
                    continue
                q = min(3, int(4 * s["step"] / L))
                err = int(not s["correct"])
                cnt[arm][q][0] += err; cnt[arm][q][1] += 1
                if arm == "JP" and q in (0, 3):
                    strata[s.get("kind", "?")][0 if q == 0 else 1][0] += err
                    strata[s.get("kind", "?")][0 if q == 0 else 1][1] += 1
    rates = {arm: {q: (c[q][0], c[q][1], round(c[q][0] / c[q][1], 6) if c[q][1] else None) for q in range(4)} for arm, c in cnt.items()}
    # Mantel-Haenszel OR (last vs first), Robins-Breslow-Greenland variance
    R = S = PR = PS_QR = QS = 0.0
    for kind, ((e1, n1), (e3, n3)) in strata.items():
        a, b, c, d = e3, n3 - e3, e1, n1 - e1
        n = a + b + c + d
        if n == 0 or (a + c) == 0:
            continue
        r_, s_ = a * d / n, b * c / n
        p, q = (a + d) / n, (b + c) / n
        R += r_; S += s_; PR += p * r_; PS_QR += p * s_ + q * r_; QS += q * s_
    OR = R / S if S else float("inf")
    if R and S:
        var = PR / (2 * R * R) + PS_QR / (2 * R * S) + QS / (2 * S * S)
        lo, hi = math.exp(math.log(OR) - 1.96 * math.sqrt(var)), math.exp(math.log(OR) + 1.96 * math.sqrt(var))
    else:
        lo = hi = None
    jp = rates["JP"]
    v = {"W1": jp[0][2] is not None and jp[3][2] >= 2 * jp[0][2],
         "W2": OR > 1.5 and lo is not None and lo > 1,
         "W3": all(rates["X5b"][q][0] == 0 for q in range(4))}
    out = {"files": len(files), "rates_by_quartile": rates, "mh_or_last_vs_first": round(OR, 4),
           "mh_ci": [lo and round(lo, 4), hi and round(hi, 4)], "strata": {k: v_ for k, v_ in strata.items()}, "verdicts": v}
    json.dump(out, open(os.path.join(HERE, "RESULTS_AGENTS2.json"), "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("files", "rates_by_quartile", "mh_or_last_vs_first", "mh_ci", "verdicts")}, indent=1))


if __name__ == "__main__":
    main()
