"""Plumbing check before a calibration (phase 1d, sealed): share of empty model replies in the traces.
Usage: python emptycheck.py smoke1d.jsonl   -> OK if at most 10% of replies are empty, else STOP (do not calibrate)."""
import sys, json
R = [json.loads(l) for l in open(sys.argv[1])]; tr = [t for r in R for t in r.get("trace", [])]
e = sum(1 for t in tr if not t["out"].strip()); ok = tr and e / len(tr) <= 0.10
print(f"replies {len(tr)}, empty {e} ({e / max(1, len(tr)):.0%}), correct {sum(r['correct'] for r in R)}/{len(R)}, errors {sum(1 for r in R if r['error'])}  ->  {'OK: run the calibration' if ok else 'STOP: harness still broken, do not calibrate'}")
for r in R[:2]:
    for t in r.get("trace", [])[:3]: print("  ", t.get("finish"), "|", t["out"][-120:].replace("\n", " / "), "|", t.get("reasoning", "")[:120])
