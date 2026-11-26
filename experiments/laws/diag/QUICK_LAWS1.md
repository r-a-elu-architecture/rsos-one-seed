# LAWS1 quick test: all laws as mathematics on twin traces (23 Nov 2026 ~05:30, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)

Development seeds 6400, 6401 only (no colour). Code: `experiments/laws/laws.py` (Part K line and every check in its
docstring, written before the first run). Traces: `diag/TRACES_LAWS1.tgz`; full numbers: `diag/QUICK_LAWS.json`,
`diag/exact.json`, `diag/sweep_p*.json`. 21 shades x 2 seeds x 6 arms = 252 traces; 2 channels each.

## Result: ROW FAILS the quick test (7 of 12 criteria pass)

| Check | Result | Criterion | Pass |
|---|---|---|---|
| EXACT (Theorem 1 independence, A1 at n = 1, 10, 50, 200, A3) | 6/6 within 3 SE (A3: MC 84.49 % vs 84.34 %, bound 81.64 %) | all | yes |
| L1′ bound | 295/298 in scope (131 channel traces out of scope: negative association, the corollary) | ≥ 90 % | yes |
| L1 read scope | 427/429 | ≥ 90 % | yes |
| L2 blind operation | 425/429 | ≥ 90 % | yes |
| C2 common point (n = T = 1) | 406/429 | ≥ 90 % | yes |
| C1 pairwise consistency | 0 conflicts in 25 ordered pairs | 0 | yes |
| PR violations predict the result | Spearman < 0 in 40/42 cells, mean −0.49 | ≥ 2/3 and < 0 | yes |
| L0 constitution (runtime) | 68/84 organism traces (16 fail: channel worse than unhealed native; 15 of them arm v2) | ≥ 90 % | **no** |
| L4 landing | 0/84; precision median 0.57 (0.14–0.80) | ≥ 90 % | **no** |
| LE error events | 163/429 (supply 28/177, drift 135/252) | ≥ 90 % | **no** |
| L3 living structure | 22/42 (keep 24/42, gradual 40/42, keeps more than native 40/42) | ≥ 90 % | **no** |
| L5 relations | 16/42 (CE differences within ±0.01 bit) | ≥ 90 % | **no** |

## Diagnosis (Part I.5: read → match → bind; a fail means the build is wrong)
- **L0:** the organism has Law 0 only at selection; Law 0's response (a runtime monitor that blocks before effect) is
  not built (Part H "membrane at runtime"). Finding, not a binding error: v2 breaks the unhealed bound in 15/42 traces.
  Landing: build the monitor (the law's response) as an arm.
- **L4:** binding error. "Need" was bound to a fixed threshold (res ≤ 1.0), not to a measured need. The organism lands
  where its fork measures a gap in the future (preventive). Landing: need = the landing's counterfactual effect
  measured by the fork (with vs without that landing), as the host measures it.
- **LE:** binding error. ε, λ were carried across seeds (different worlds); the law predicts from the host's own ε, λ.
  Landing: estimate on half of the units of the same world, check on the other half.
- **L3:** binding error. "The round's damage" was read after the heals (net onsets), so every level counted as inside
  the threshold. Landing: damage = expected new drift per tick from the pre-tick state.
- **L5:** binding error. The no-relation baseline already contained the strongest relation of this world (the
  supply↔drift link of the same unit). Landing: baseline = no relation; R = link + graph neighbours.

Checks of LAWS1 are not changed. LAWS2 (`laws2.py`) carries these landings, written before its run, on new development
seeds 6410, 6411.
