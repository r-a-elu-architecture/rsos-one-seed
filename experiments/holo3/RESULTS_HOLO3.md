# HOLO3 results (private, 21 Nov 2026, (UTC+02:00) Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)

Sealed first: `SEAL_HOLO3.txt` (commit 9da1bb4). Raw: `RESULTS_HOLO3.json`. 120 orders x 5 densities x 8 seeds.

## Scored exactly as sealed
| ID | Result | Verdict |
|---|---|---|
| P3 the law under recombination | in **120 of 120 orders** a trigger on one process's O changed all five of its subnodes; it changed **44-47 of the 49 other processes** (median 46) | **PASS** |
| P2 advantage grows with relation density | median order minus best baseline: d1 -0.07, d2 -0.28, d3 -0.62, d4 -0.33, d5 -0.54; Spearman -0.09, p = 0.59 | **FAIL** |
| P2b coupled beats uncoupled at d = 5 | 3 of 8 seeds, p = 0.86 | **FAIL** |
| P1 same structure at two levels (seen before seal) | Spearman 0.62, null 95 % 0.77, p = 0.096 | **FAIL** (not blind) |

G per density (higher is better; RR / history / quark median order / quark best order / uncoupled):
d1 -4.32 / -4.27 / -4.27 / -4.21 / -4.26 · d3 -10.02 / -9.86 / -10.18 / -10.03 / -10.16 · d5 -17.06 / -17.58 /
-17.28 / -17.13 / -17.22. The best order is picked after the run (selection), so it is not a claim.

## Exploratory (observed after the run, to be sealed before reuse)
**The order (the program) matters more as the relation space grows.** Spread of G across the 120 orders:
d1 0.129 · d2 0.198 · d3 0.306 · d4 0.481 · d5 0.845, i.e. 1.0x, 1.5x, 2.4x, 3.7x, 6.5x. In HOLO2 (no relations)
the spread was smaller than noise. This matches "hot = possibilities in relations": the more relations, the more
the recombination of V, A, K, O, G changes the outcome. Candidate for the next seal: order spread rises with
relation density on a new host.

## Reading (fever principle)
- The law's consequence held where it was tested directly: a change in one subnode reaches the whole quark under
  every order and spreads through almost every other process (P3), now in a host rich in relations.
- The assembly is not yet right for G: my priority weights (set by me) did not beat round-robin, and the chain did
  not beat the same parts summed. Order spread (above) shows the program space is real; the next step is to find
  the program that fits the host, sealed before testing, not to tune after seeing.
