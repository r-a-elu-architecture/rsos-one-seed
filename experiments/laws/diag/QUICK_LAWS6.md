# LAWS6 short test: row 1 with K.17 (24 Nov 2026, commit time exact; UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Dev seeds 6670, 6671; shades 1, 4, 7, 10, 13, 16, 19 (14 cells). Code `laws6.py` (6236e7a, before the run).

## Result: 10 of 13 pass (LAWS5: 10/13; different three now) → step 1 for L0, LE, L3
| Check | LAWS5 | **LAWS6** | Pass |
|---|---|---|---|
| L4 landing | 12/14, median 0.971 | **14/14, median 0.987** | **yes** |
| L5 relations (pair under stress) | 5/7 | **7/7** | **yes** |
| RC cost / margin | 14/14 · 14/14 | 14/14 · 14/14 | yes |
| PR violations predict the result | 13/14, ρ −0.58 | **14/14, ρ −0.84** | yes |
| L1′, L1, L2, C2, C1, EXACT | pass | pass | yes |
| L0 constitution | 13/14 | 12/14 | **no** |
| LE error events | 38/46 | 37/42 (88.1 %) | **no** |
| L3 living structure | 13/14 | 11/14 (keep 14, gradual 14, ≥ native 11) | **no** |
Events (v5m): 1,303 withheld, 48 re-targeted, 0 refused, 243 gated.

## Data for step 1
- **L0:** both fails are cells where the unhealed native never had a dry unit (bound maxdry = 0): one dry tick of the
  organism breaks it; the gate (now never landing defaults) found no candidate that keeps 0 (shade 1 seed 6670: 4
  ticks; shade 13 seed 6671: 15 ticks).
- **LE:** 5 fails, measured above predicted by 0.03–0.07, 4 of them the drift channel (3 the native arm): an element's
  behaviour on replay 1 transfers to replay 2 only within that margin when the policy's heals and the visits differ.
- **L3:** the 3 fails are drop(v3r) − drop(native) = +0.002, 0.000, +0.004: ties at the margin, keep 14/14, gradual 14/14.
