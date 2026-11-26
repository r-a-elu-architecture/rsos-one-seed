# ORG-REAL2: structure transfer on real data, the field's standard rule (owner "seal", 22 Nov 2026 10:10), sealed before run
Code real7.py = real6.py with only: barrier capped at 20 % of the training examples (size-scaled; fixes the iris signal
of ORG-REAL1), fresh seeds (selection 12000-12001, evaluation 12100-12107, random 12200+), output files RAW7 (diff
below). Hosts, structures, arms and the 9 noisy-label baselines (given the true noise rate) as PREREG_REAL1.md.
Fixed-sequence tests over the 64 rows (one-sided sign tests, ties dropped; a step counts only if all previous pass):
 1 Control: own > rnd_own, p < 0.05.
 2 Transfer: tr > rnd_tr, p < 0.05.
 3 Primary (standard rule): tr > EACH of the 9 baselines, Holm over the 9, every adjusted p < 0.05.
Reported: tr vs per-run best of 9 (the ORG-REAL1 bar), by dataset, by noise kind, iris alone, structures chosen.
Colour rule: if 1-3 pass, the structure-transfer finding is confirmed in layer 1 and becomes CYAN (layer 2: ORG5 and
ORG-FINAL); Biology and Level C get blue on their real-data parts (the rows stay yellow until their shades pass).
Otherwise no colour change. No further seeds after this run. Smoke: none needed beyond the unchanged ORG-REAL1 code
paths plus one call of the new barrier on seed 996.
1c1
< """ORG-REAL1: the family structure on real data against the field's noisy-label methods (owner "1", 22 Nov 2026 07:27).
---
> """ORG-REAL2 (= real6.py with: barrier capped at 20 % of the training examples (size-scaled, iris fix), fresh seeds, RAW7 files; owner "seal" 22 Nov 2026 10:10). ORG-REAL1: the family structure on real data against the field's noisy-label methods (owner "1", 22 Nov 2026 07:27).
33c33
< SEL, EV = [11000, 11001], list(range(11100, 11108))
---
> SEL, EV = [12000, 12001], list(range(12100, 12108))
57a58,63
> def barrier_mask(mem):
>     """barrier, size-scaled: examples misclassified persistently (memory > 3), at most 20 % of the training set."""
>     s = mem > 3; cap = int(np.ceil(0.2 * len(mem)))
>     if s.sum() > cap: m = np.zeros(len(mem), bool); m[np.argsort(-mem)[:cap]] = True; s &= m
>     return s
> 
63c69
<         bt = batches[t]; sus = mem > 3 if st["barrier"] else np.zeros(len(Xtr), bool)
---
>         bt = batches[t]; sus = barrier_mask(mem) if st["barrier"] else np.zeros(len(Xtr), bool)
104c110
<     json.dump(out, open(f"RAW6_select_p{part}.json", "w"))
---
>     json.dump(out, open(f"RAW7_select_p{part}.json", "w"))
108c114
<     for f in sorted(glob.glob("RAW6_select_p*.json")): T.update(json.load(open(f)))
---
>     for f in sorted(glob.glob("RAW7_select_p*.json")): T.update(json.load(open(f)))
113c119
<             rng = np.random.default_rng(11200 + 10 * HOSTS.index(h) + i)
---
>             rng = np.random.default_rng(12200 + 10 * HOSTS.index(h) + i)
119c125
<     json.dump(rows, open(f"RAW6_eval_p{part}.json", "w"))
---
>     json.dump(rows, open(f"RAW7_eval_p{part}.json", "w"))
