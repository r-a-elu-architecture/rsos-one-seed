# SEC1 v3 results (sealed 898873b; fresh seeds)

## Organism v3 (80 worlds, seeds 7400-7415 x d1-5)
| Prediction | v2 | v3 | Holm p (v3) | Level |
|---|---|---|---|---|
| P0 > unhealed | 79/80, +0.019 | 80/80, +0.034 | 5e-24 | exceptional |
| P1 structure carries | 76/78 | 75/76 (24.6 vs ~0.7 units) | 4e-21 | exceptional |
| P2 > global same size | 80/80, +0.117 | 80/80, +0.135 | 5e-24 | unprecedented in series (now 368/368 across hosts) |
| P5 > best native | 51/80, +0.002 | 74/80, +0.014 | 8e-16 | exceptional |
| P7 > same hosts apart | 5/79 (fail) | 62/80, +0.004 | 8e-7 | high (pass) |
| P3 gain grows with density | rho -0.05 | rho +0.13 | 0.13 | fail (direction now right, not significant) |
Program chosen per tick: hosts' own (B) 7500, organism's own whole (A) 1818, default (C) 282. Disclosed: B is inside
the candidate set; the gain over apart comes from the 22 % of ticks where reading the whole chose another program.
Transpersonal landings (local loss for whole gain) in A: mean 9.2 per world.

## Real data v3 (48 runs, seeds 7500-7515)
| Prediction | v2 | v3 | p | Result |
|---|---|---|---|---|
| P0 > plain SGD | 5/33 (reversed) | 10/23, mean -0.0015 | 0.80 | fail (no longer reversed) |
| P2 > global | 8/32 (reversed) | 12/23, mean -0.0010 | 0.50 | fail (neutral) |
| P5 > best native | 2/39 (reversed) | 6/29, mean -0.0049 | 0.9997 | fail |
Landings kept per run: cancer 25, wine 64, digits 30 of 300. Signal: the defects were real (reversal removed), but on
these small, nearly separable datasets (plain SGD at 0.94-0.99) the 4 extra examples per step carry almost no lack to
heal. Blue cells: no change.
