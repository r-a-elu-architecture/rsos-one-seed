# HOLO6 results (sealed; fresh seeds 500-515, same 80 worlds as HOLO4/HOLO5)

| | HOLO4 (global knobs) | HOLO5 (bucketed address) | HOLO6 (particle at the letter) |
|---|---|---|---|
| Mean advantage vs best baseline, d1 | -0.06 | -0.06 | **+0.09** (12/16 wins) |
| d2 | -0.26 | -0.22 | **+0.04** (11/16) |
| d3 | -0.66 | -0.50 | -0.03 (8/16) |
| d4 | -0.51 | -0.54 | **+0.18** (11/16) |
| d5 | -0.99 | -0.94 | -0.11 (9/16) |
| W1 beats best baseline at d5 | 4/16 fail | 3/16 fail | 9/16, p 0.40 fail |
| W2 grows with density | rho -0.26 fail | rho -0.34 fail | rho +0.07, p 0.53 fail (no longer shrinks) |
| W3 coupled beats summed d5 | 8/16 fail | 5/16 fail | 8/16 fail |
| W4 beats unhealed | 37/80 fail | 0/80 fail | **80/80, p 8e-25 pass** |
| W5 beats HOLO4 knobs | — | 43/80 fail | **69/80, p 1e-11 pass** |

Exploratory (not sealed): live landing beats the best baseline in 51 of 80 worlds pooled (one-sided sign p 0.009).
Particles landed at 1,491 of 14,942 disagreeing letters (10.0 %); 41,980 futures were run.
Layer note: the futures are the world's own (layer 2: frozen and copied). A layer-1 scheduler needs a model of the future.
