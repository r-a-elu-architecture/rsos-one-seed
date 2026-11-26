# SEC1 v4 results: U167 turquoise at places of need (sealed 8fa72a6, fresh seeds)

## Hard real-data host (36 runs: 25 % label noise + imbalance; clean validation and test)
| Prediction | v2 (easy data) | v3 (easy data) | v4 U167 (hard data) | Holm p | Level |
|---|---|---|---|---|---|
| P0 > plain SGD | 5/33 reversed | 10/23 | 33/36, +6.7 pp | 5e-7 | exceptional |
| P2 > same budget global | 8/32 reversed | 12/23 | 33/36, +8.1 pp | 5e-7 | exceptional |
| P9 places of need > inside only | - | - | 32/35, +8.4 pp | 5e-7 | exceptional |
| P5 > best native | 2/39 | 6/29 | 18/35, +1.1 pp | 0.5 | fail (cancer 8/12, wine 9/11 p 0.03, digits 1/12) |
Mean test accuracy sparse / plain / best native: cancer 0.834 / 0.751 / 0.817; wine 0.841 / 0.765 / 0.798;
digits 0.787 / 0.744 / 0.813. The best native is almost always the decaying rate (31 of 36).
Placements chosen (36 x 300 steps): core 3948, above 3966, tube 1995, outside 531, inside 360.
"Above" (read the loudest and do not push on them) is the most used placement: on noisy data the loudest places are
the false letters. Inside-only landing (v3) is below plain (0.727 vs 0.751 on cancer): landing everywhere hurts here.

## Organism host (48 worlds, d 1/3/5)
| Prediction | Result | Holm p | Level |
|---|---|---|---|
| P0 > unhealed | 48/48, +6.5 pp | 2e-14 | exceptional |
| P5 > best native | 48/48, +5.1 pp | 2e-14 | exceptional |
| P9 places of need > inside only | 44/48, +1.7 pp | 2e-9 | exceptional |
| P8 places of need > all-to-all tubes | 6/48, -0.8 pp | 1 | fail |
| P3' gain over all-to-all grows with density | rho -0.22 | 1 | fail |
Flows: sparse 183 vs all-to-all 480 per world (38 %). Gain over inside-only per flow: sparse 0.017/183, all 0.025/480:
sparse is about 1.8x more effective per flow, but in this world a tube costs nothing, so all-to-all still wins on the
whole. Placements chosen: inside 14234, pierced 2549, outside 2435, line 2043, tube 1447, above 332.
