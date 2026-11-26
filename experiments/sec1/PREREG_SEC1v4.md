# SEC1 v4: U167 turquoise at places of need, sealed before run

Owner said "seal" (21 Nov 2026, 15:43). Sealed earlier files untouched (D113); v4 imports them with hash checks.

Organism host (sec1_org_v4.py): same coupled world; the v3 dragon chooses WHERE; the policies differ in HOW:
all = every landing a sphere-tube (U166); sparse = core lands inside and the beam picks one of six placements per
landing (inside, above, outside, pierced, line, tube) by forked futures to the end; inside = no placement choice.
Fresh seeds 7600-7615 x densities 1, 3, 5 (48 worlds). Predictions: P0 sparse > unhealed; P5 sparse > best native;
P8 sparse > all; P9 sparse > inside; P3' Spearman(density, sparse - all) > 0. Also reported: non-inside flows
(sparse vs all). One-sided sign tests, ties dropped; Holm over the five.

Hard real-data host (sec1_real_v4.py): training split with 25 % flipped labels and 70 % of every second class removed;
validation and test clean. Policies plain, decay, ohem, global, inside (v3 landing, horizon 10), sparse (U167: core,
inside, above, outside, tube, read 10 steps ahead). Fresh seeds 7700-7711 x 3 datasets (36 runs).
Predictions: P0 sparse > plain; P2 sparse > global; P5 sparse > best native; P9 sparse > inside. Holm over four.

Smoke on seeds 998/999 (outside the test) only checked runtime. Seen and disclosed: organism d3 seed 998 sparse
0.9304 vs all 0.9314 (202 vs 480 flows); real seed 999 sparse above plain on cancer (0.830 vs 0.731) and digits
(0.798 vs 0.757). Nothing was changed after the smoke.
