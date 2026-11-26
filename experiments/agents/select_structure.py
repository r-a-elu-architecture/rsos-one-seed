"""Phase 1 decision (exploratory, one cheap model, warehouse family): choose the RSOS structure with the highest
accuracy; kill switch: continue only if that structure beats react by at least 3 accuracy points.
Usage: python select_structure.py phase1.jsonl"""
import sys, json, collections
R = [json.loads(l) for l in open(sys.argv[1])]; acc = collections.defaultdict(list); last = {}
for r in R: last[(r["model"], r["arm"], r["task"])] = r  # a re-run replaces an earlier errored row
for r in last.values(): acc[r["arm"]].append(r["correct"])
print("rows with infrastructure errors (counted as wrong):", sum(1 for r in last.values() if r["error"]))
tab = {a: sum(v) / len(v) for a, v in acc.items()}
for a, x in sorted(tab.items(), key=lambda z: -z[1]): print(f"{a:14s} {x:.3f}  (n={len(acc[a])})")
best = max((a for a in tab if a.startswith("rsos_")), key=lambda a: (tab[a], a))
go = tab[best] >= tab.get("react", 1) + 0.03
print(f"\nchosen structure: {best}  ({tab[best]:.3f} vs react {tab.get('react', float('nan')):.3f})  ->  {'CONTINUE' if go else 'STOP (kill switch)'}")
json.dump({"chosen": best, "continue": go, "accuracy": tab}, open("PHASE1_DECISION.json", "w"), indent=1)
