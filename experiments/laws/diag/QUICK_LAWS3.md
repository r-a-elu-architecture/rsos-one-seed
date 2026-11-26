# LAWS3 quick test (23 Nov 2026 ~08:20, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)

Development seeds 6420, 6421. Code `laws3.py` (pushed before the run, 761d88f). Numbers `QUICK_LAWS3.json`; traces
`TRACES_LAWS3.tgz`.

## Result: ROW FAILS (9 of 13 criteria pass)
| Check | Result | Pass |
|---|---|---|
| EXACT | 6/6 | yes |
| **L0 constitution (v3m: budget-correct P1 + membrane, protect last)** | **42/42**; channel-bound breaks: v2 0, v3 0, v3m 0, own6 3, round 34, random 42 traces | yes |
| Budget (finding) | overruns: **v2 (sealed ORG7 organism) 18 ticks in 13 traces**; v3, v3m and all others 0 | — |
| RC cost of the responses | G(v3m) ≥ G(v3) − 0.01 in 41/42; v3m > best native and beam-only in 42/42 | yes |
| L1′ / L1 / L2 | 404/408 · 522/523 · 518/523 | yes |
| C2 / C1 | 493/523 · 0 conflicts in 25 pairs | yes |
| PR violations predict result | 42/42 cells negative, mean ρ −0.78 | yes |
| L4 landing (v3m made landings) | **0/42**; made precision median 0.55 (473 re-targets, 295 gates); tried precision: v3 0.43, report+popular 0.50, random 0.30 | **no** |
| LE error events (odd/even units, domain T ≤ τ/2, 2 SE + 0.01) | 214/523; errors symmetric, ±0.03–0.12 at T = 2 | **no** |
| L5 relations (leave one shade out) | 15/21; |CE_R − CE_0| ≤ 0.0023 bit everywhere | **no** |
| L3 living structure | 31/42 (keep 36, gradual 38, keeps more than native 38) | **no** |

## Reading
- Three loops converge on the same picture: the **law set is consistent (0 conflicts in every loop) and predictive
  (violations ↔ lower result, 40/42, 42/42, 42/42 cells)**; Laws 1′, 1, 2 hold in ≥ 98 % of traces in every loop;
  Law 0 holds 42/42 once its response is built in the right order.
- **L4:** in this host about half of all landings (every policy, organism included) change nothing measurable in
  the projected future, and in most such ticks no unit has a measured need to re-target to. Whether a landing
  without a measured need should be withheld ("nothing is pushed", SEED_V3) or may be preventive is the owner's
  operator definition, not a binding to choose after seeing results.
- **LE:** units of one world are different hosts (heterogeneous ε, λ); the law's parameters do not transfer between
  units, so the odd/even test checks heterogeneity, not the law. Within one unit the linear form is the union bound
  (an identity bound), so a non-trivial fresh-trace test needs the same element on a fresh run.
- **L5:** under the organism, drifted neighbours are rare, so the relation carries ≤ 0.002 bit about onsets; the
  binding to onset prediction is too weak to show the limit. MATH_V1 §7's form is reading a partly lost state.
- **L3:** a genuine partial pass.
