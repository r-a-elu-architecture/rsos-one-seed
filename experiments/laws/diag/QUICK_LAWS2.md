# LAWS2 quick test (23 Nov 2026 ~06:50, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)

Development seeds 6410, 6411 (dry run on throwaway 6499, not kept). Code `laws2.py` (written and pushed before the
run, commit "LAWS2 build written before its run"). Numbers: `QUICK_LAWS2.json`; traces `TRACES_LAWS2.tgz`.

## Result: ROW FAILS (8 of 13 criteria)
| Check | Result | Pass |
|---|---|---|
| EXACT | 6/6 | yes |
| L1′ bound | 405/410 | yes |
| L1 read scope | 511/511 | yes |
| L2 blind operation | 511/511 | yes |
| C2 common point | 486/511 | yes |
| C1 consistency | 0 conflicts / 30 pairs | yes |
| PR violations predict result | 42/42 cells negative, mean Spearman −0.78 | yes |
| L4 landing (v2m, effects through the membrane) | 42/42 (tried-landing precision medians: v2 0.63, v2m 0.61, own6 0.55, report+popular 0.50, round 0.35, random 0.31) | yes |
| L0 constitution (v2m) | 26/42 (traces with a channel above the bound: v2 2, **v2m 8**... counted per trace: v2m 16 fail) | **no** |
| RC cost of the responses | G(v2m) ≥ G(v2) − 0.01 in 31/42; margin over best native 40/42 | **no** |
| LE error events (odd/even units) | 93/511; median meas − pred ≈ 0 at T = 2, 4; −0.07 (supply), −0.03 (drift) at T = 8 | **no** |
| L3 living structure | 29/42 (keep 37, gradual 37, keeps more than native 33) | **no** |
| L5 relations (fit one seed, test other) | 13/42; with-relation CE higher in 29/42 (overfit, ≤ 0.02 bit) | **no** |

## Diagnosis
- **L0 / RC: build-order error.** The membrane gated Law 0 first, then removed the landings without measured need
  (Law 4), so the final action was never checked against Law 0; dropping landings also cost G (11/42 cells lose >
  0.01). Part 0.3 U157: the order is the program — protect must come last; and Law 4 says land where needed, i.e.
  re-target, not withhold.
- **LE: check-design error.** The tolerance ignored sampling error (15 units x 60 ticks per half) and T = 8 lies
  outside the linear law's stated domain (MATH_V2 A2: T ≪ τ̄). The law is unbiased in its domain (median ≈ 0).
- **L5: estimation error.** An 8-cell table fit on one 60-tick world overfits; the relation is weak per sample
  (drifted neighbours are rare under the organism). Needs a pooled fit (leave one shade out).
- **L3:** keeps the state and degrades gradually in most traces; 9/42 lose more than the native: the organism's
  margin shrinks under damage there. Recorded as found; not rebound.
