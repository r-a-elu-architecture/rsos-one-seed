"""Read the rsos2 quick test (development seeds staff 6000-6029, orders 4000-4029; NOT confirmatory).
Usage: python quick2_read.py quick2_staff.jsonl quick2_orders.jsonl   (candidate arm: env CAND, default rsos2; quick3: CAND=rsos3)
Go rule for sealing the long run (fixed 23 Nov 03:20, before any quick-test call):
  G1 rsos2 gives no answer at most as often as react + 2 (per model, pooled over families)  -> the budget failure is fixed
  G2 rsos2 wins >= losses against react, pooled                                            -> no harm on development tasks
  G3 plumbing: 0 infrastructure errors after resume
Reported, not gated: react vs react_b discordance (the noise floor), provider counts, tokens and cost per run."""
import sys, json, collections, os
C = os.environ.get("CAND", "rsos2")
last = {}
for p in sys.argv[1:]:
    for l in open(p):
        r = json.loads(l); last[(r["model"], r["arm"], r["task"])] = r
models = sorted({m for m, a, t in last}); arms = ["react", "react_b"] + sorted({a for m, a, t in last if a.startswith("rsos")})
def rows(m, a): return [r for (mm, aa, t), r in last.items() if mm == m and aa == a]
def pair(a, b, m=None):
    ks = {(mm, t) for (mm, aa, t) in last if aa == a and (m is None or mm == m)}
    w = l = 0
    for mm, t in ks:
        x, y = last.get((mm, a, t)), last.get((mm, b, t))
        if not x or not y: continue
        w += x["correct"] and not y["correct"]; l += y["correct"] and not x["correct"]
    return w, l
ok = True
for m in models:
    print("\n" + m)
    for a in arms:
        rs = rows(m, a)
        if not rs: continue
        na = sum(r["given"] in (None, "") for r in rs); er = sum(bool(r["error"]) for r in rs)
        print(f"  {a:8s} n={len(rs):3d} acc={sum(r['correct'] for r in rs)/len(rs):.3f} no-answer={na:2d} errors={er} "
              f"mean calls={sum(r['calls'] or 0 for r in rs)/len(rs):.1f} mean tokens={sum(r['tokens'] or 0 for r in rs)/len(rs):,.0f}")
    na = {a: sum(r["given"] in (None, "") for r in rows(m, a)) for a in arms}
    g1 = na[C] <= na["react"] + 2; ok &= g1
    print(f"  G1 no-answer {C} {na[C]} vs react {na['react']}: {'PASS' if g1 else 'FAIL'}")
    for a in arms[2:]: print(f"  {a} vs react {pair(a,'react',m)}  vs react_b {pair(a,'react_b',m)}")
    print(f"  noise floor react vs react_b {pair('react','react_b',m)}")
w, l = pair(C, "react"); g2 = w >= l; ok &= g2
print(f"\nG2 pooled {C} vs react wins/losses {w}/{l}: {'PASS' if g2 else 'FAIL'}   (vs react_b {pair(C,'react_b')})")
nw, nl = pair("react", "react_b"); print(f"noise floor (react vs react_b, pooled): {nw}/{nl} discordant = {nw+nl}")
errs = sum(bool(r["error"]) for r in last.values()); g3 = errs == 0; ok &= g3
print(f"G3 infrastructure errors {errs}: {'PASS' if g3 else 'FAIL (re-run the same command to resume)'}")
tok = collections.Counter()
for (m, a, t), r in last.items(): tok[m] += r["tokens"] or 0
print("tokens per model:", dict(tok))
print("\nGO to seal the long run" if ok else "\nNO GO: fix before sealing")
