# SPHERE2: SPHERE1's open predictions with enough samples (layer 2), sealed before any SPHERE2 code

Written 20 Nov 2026, ~08:00 Vilnius. Private. SPHERE1 (`../sphere/RESULTS_SPHERE1.md`) failed S1 and S8 because ε was
estimated from 400 operations. Same nodes, same code (`../sphere/sphere1.py` functions), larger samples; the true ε of
N5 and N7 is known by construction and is **not** used by the predictions below except where stated as theory.

## Samples

N2, N3, N5, N6, N7: 20,000 one-key and 20,000 two-key operations; 4,000 condition and 4,000 scan operations per node.
Classification uses the 95 % interval of (pair − key): **element** if its lower bound exceeds ε / 4, **time** if its
upper bound is below ε / 4.

## Predictions

| # | Prediction |
|---|---|
| T1 | Classes: N2 network element; N3 ledger time; N5 chemistry element; N6 orbit time |
| T2 | N5 chemistry: condition failure within 2 pp of 1 − (1 − ε̂)^50, ε̂ from its one-key operations |
| T3 | N6 orbit (theory of time windows, MATH_V1 §5): failure for n reads = (30 + 0.01·(n − 1)) / 100 within 1 pp for n = 1, 2, 50, 300 |
| T4 | N7 slots (Theorem 1's corollary): condition failure exceeds 1 − (1 − ε̂)^50 by at least 1.5 pp, ε̂ from its one-key operations; theory: 84.3 % against 81.6 % |
| T5 | Cross-node healing (N1 with 30 % of facts known from N3), scenes 1030–1045: the unknown facts gain ≥ 5 pp at 85 % erasure and ≥ 3 pp at 95 % |

Every prediction reported pass or fail; nothing changed after the run.
