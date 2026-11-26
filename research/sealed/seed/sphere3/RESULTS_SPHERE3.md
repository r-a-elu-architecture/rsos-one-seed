# SPHERE3 results (layer 2), private

Predictions: `PREREG_SPHERE3.md` (commit 3846383). Code: `sphere3.py` (commit e60eff5, before any result). Data:
`RESULTS_SPHERE3.json`. Run 20 Nov 2026, ~08:45 Vilnius. 8,000 condition operations of 50 reads per node; ε measured
inside the same operations (400,000 element observations per node).

## Strongest finding

**Theorem 1 and its predicted exception hold exactly where the mathematics says.** The compounding bound is reached
when errors are independent, undercut when they cluster, and **exceeded when successes compete** — as the corollary
predicted before the run:

| Node | How its successes relate | Joint failure | Bound 1 − (1 − ε̄)^50 | Gap |
|---|---|---|---|---|
| N5 chemistry | independent | 60.60 % | 60.41 % | +0.19 pp (± 0.55) |
| N2 network | positively associated (bursts) | 56.18 % | 63.75 % | −7.58 pp (± 0.56) |
| N3 ledger | positively associated (outages) | 99.20 % | 100.0 % | −0.80 pp (± 0.10) |
| **N7 slots** | **negatively associated (competing)** | **84.38 %** | **81.56 %** | **+2.82 pp (± 0.41), about 7 standard errors** |

## Predictions: 3 pass, 1 fail

| # | Result |
|---|---|
| U1 N5 within 1 pp of the bound | **pass** (+0.19) |
| U2 N7 above the bound by ≥ 1.5 pp | **pass** (+2.82; theory +2.7) |
| U3 N2 and N3 below the bound by ≥ 5 pp | **fail**: N2 −7.58 (pass), N3 −0.80: the ledger fails almost always at n = 50, so nothing is left to fall below |
| U4 the bound holds on N2, N3, N5 | **pass** |

## Meaning

Law 1′ is now a theorem confirmed on both sides of its condition: it holds where successes are independent or
positively associated, and fails where they are negatively associated, by the predicted amount. SPHERE2's T4 failed
only because ε was estimated from a different family.
