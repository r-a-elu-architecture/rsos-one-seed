# SPHERE3: Theorem 1 and its corollary tested directly (layer 2), sealed before any SPHERE3 code

Written 20 Nov 2026, ~08:40 Vilnius. Private. SPHERE2 showed that estimating ε from a separate family amplifies its
error about 9× at n = 50. Here ε is measured **inside the same operations**: every one of the 50 elements of every
condition operation is observed (read or not), so the per-element failure rate ε̄ comes from 50 × 8,000 = 400,000
element observations, and the bound 1 − (1 − ε̄)^50 is compared with the operations' joint failure.

Nodes (from SPHERE1/2): N2 network (bursts), N3 ledger (outages), N5 chemistry (independent), N7 slots (exactly 10 of
300 elements down per epoch). 8,000 condition operations each; all 50 reads of an operation are attempted (no early
stop), so each element is observed.

## Predictions

| # | Prediction |
|---|---|
| U1 | N5 (independent): joint failure within 1 pp of the bound |
| U2 | N7 (negatively associated): joint failure **above** the bound by ≥ 1.5 pp (theory 84.3 % vs 81.6 %) |
| U3 | N2 and N3 (positively associated): joint failure **below** the bound by ≥ 5 pp |
| U4 | Theorem 1 overall: on every node except N7, joint failure ≤ bound + 1 pp |

Every prediction reported pass or fail; nothing changed after the run.
