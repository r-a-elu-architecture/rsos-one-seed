# LAWS5 short test: row 1 with K.8 + K.16 (24 Nov 2026, commit time exact; UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Dev seeds 6630, 6631; shades 1, 4, 7, 10, 13, 16, 19 (14 cells). Code `laws5.py` (93c5fa9, before the run).

## Result: 10 of 13 pass (LAWS4: 8 of 13) → the three fails go back to step 1
| Check | LAWS4 | **LAWS5** | Pass |
|---|---|---|---|
| L0 constitution | 16/16 | 13/14 (shade 16, seed 6631: 9 ticks above the bound) | yes (≥ 90 %) |
| L4 landing | 9/16, median 0.913 | **12/14, median 0.971** (the 2 fails: shade 16, both seeds, 0.82) | **no** (85.7 %) |
| RC cost of the responses | 14/16 | **14/14, margin 14/14** | yes |
| LE error events | 74/102 | 38/46 (82.6 %) | **no** |
| L5 relations | 10/21 (≤ 0.003 bit) | 5/7 (up to 0.0047 bit) | **no** |
| L3 living structure | 35/42 | **13/14** (keep 14, gradual 14, ≥ native 13) | yes |
| L1′ / L1 / L2 / C2 | pass | 108/108 · 147/148 · 145/148 · 140/148 | yes |
| C1 / PR / EXACT | pass | 0 conflicts · 13/14 cells, ρ −0.58 · 6/6 | yes |
Events (v5m): 1,162 withheld, 63 re-targeted, 8 refused, 196 gated.

## Data for step 1
- **L4 (and the L0 ticks):** both L4 fails and all 9 L0 ticks are shade 16: the Law 0 gate's fallback lands an action
  (defaults) whose landings have no measured need and can still project above the bound.
- **LE:** all 8 fails are the drift channel, measured ABOVE predicted (+0.03 … +0.10), mostly the native arm: up-times
  are not geometric (heals reset the hazard, neighbours spread drift), so a constant per-element hazard under-predicts.
- **L5:** the coupled pair carries information now (5/7, ΔCE up to −0.0047 bit) but little: under the organisms few
  units drift, so the partner's state rarely says anything.
