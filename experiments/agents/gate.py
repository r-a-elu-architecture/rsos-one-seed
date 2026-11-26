"""Difficulty gate (phase 1b, sealed): on the calibration seeds, react must be between 0.30 and 0.80 accuracy, so the
selection family has room for a structure to help or hurt. Outside that band the family is rejected before any decision.
Usage: python gate.py calib.jsonl"""
import sys, json
R = [json.loads(l) for l in open(sys.argv[1])]; last = {}
for r in R: last[(r["model"], r["arm"], r["task"])] = r
v = [r["correct"] for r in last.values() if r["arm"] == "react"]; acc = sum(v) / len(v)
ok = 0.30 <= acc <= 0.80
print(f"react on calibration: {acc:.2f} (n={len(v)}, errors {sum(1 for r in last.values() if r['error'])})  ->  {'PASS: run phase 1b' if ok else 'REJECT: family out of band, do not run phase 1b'}")
