# SPHERE2 results (layer 2), private

Predictions: `PREREG_SPHERE2.md` (sha256 `667619b5…0e50`, commit aa80b3f). Code: `sphere2.py` (before any result).
Data: `RESULTS_SPHERE2.json`. Run 20 Nov 2026, ~08:10 Vilnius.

## Strongest finding

**The time-window law predicts the orbit node to within 1 pp at every scope.** Failure = (30 + 0.01·(n − 1)) / 100:
predicted 30.0 / 30.01 / 30.49 / 32.99 %, observed 29.84 / 29.97 / 30.55 / 32.95 % for 1 / 2 / 50 / 300 reads
(20,000 and 4,000 operations). A law derived from the real SQLite failure (OPS2) predicted a different host exactly.

## Results: 1 pass, 4 fail

| # | Result | Measured |
|---|---|---|
| T1 classes | **fail** | N2 element ✓, N5 element ✓, N6 time ✓, **N3 ledger element** (predicted time): each read takes its own epoch, so an operation spans n epochs |
| T2 chemistry within 2 pp of the bound | **fail** | 61.65 % against 59.05 % (+2.6 pp); with the true ε the bound is 60.3 % (+1.35 pp) |
| T3 orbit within 1 pp of the time-window law | **pass** | largest gap 0.16 pp |
| T4 slots exceed the bound by ≥ 1.5 pp | **fail** | 83.65 % against 83.84 %; ε̂ = 3.58 % (true 3.33 %) |
| T5 cross-node healing | **fail** (as one row) | 85 % erasure: +6.3 pp (75.55 → 81.87; pass); 95 %: +2.98 pp (40.61 → 43.59; predicted ≥ 3) |

## Diagnosis

1. **The bound amplifies the error of ε̂.** At n = 50 the bound moves about 9 × as fast as ε: a 0.25 pp error in ε̂ (1.9
   standard errors, from 20,000 operations) shifts the bound by 2.2 pp, as large as the corollary's predicted excess
   (2.7 pp). T2 and T4 cannot be decided this way. The right test compares each operation's joint success with the
   product of its own elements' measured marginals (no ε̂ from a separate family).
2. The ledger prediction was a conceptual error: its outages persist, but every read occupies a new epoch, so errors
   belong to epochs and accumulate with scope (element class by the rule).
3. Cross-node healing is real and grows where information survives (+6.3 pp at 85 %; +3.0 at 95 %).
