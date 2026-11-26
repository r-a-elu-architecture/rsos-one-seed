# SPHERE1: the nodes of the seed connected in one run (layer 2), sealed before any SPHERE1 code

Written 20 Nov 2026, ~07:30 Vilnius. Private. Theory: `../math/MATH_V1.md` (committed 3fe62f1 before this file).
Protocol: `../protocol/protocol_v0.py` (3e764f7). Every node is built on the seed's anatomy (component, operator,
grammar, host, mirror) and speaks protocol v0.

## Nodes

| Node | Host | What its errors belong to (theory, §5) |
|---|---|---|
| N1 Memory | holographic store, plain reading, 30 % erasure per operation | elements (independent) |
| N2 Network | Gilbert–Elliott burst loss (as OPS1), one retry; carries every message between nodes | elements (clustered) |
| N3 Ledger | 5 replicas in 2 racks with outages (as OPS1) | elements (clustered) |
| N4 Database | real SQLite with a writer holding locks (as OPS2) | time windows |
| **N5 Chemistry (new)** | each element read by sampling marker molecules (Poisson, mean 4); a read fails when no molecule is drawn | **predicted: elements (independent)** |
| **N6 Orbit (new)** | a relay satellite visible 70 of every 100 time units; an operation fails if any of its reads falls outside a pass; reads take 0.01 units | **predicted: time windows** |
| **N7 Slots (new)** | in every epoch exactly 10 of the 300 elements are unavailable (maintenance), drawn without replacement | **predicted: negatively associated successes** |

Operations: one key (n = 1), two keys (2), condition (50), scan (300); 400 per family per node (N1: 200).

## Predictions

| # | Prediction |
|---|---|
| S1 | **Law transfer.** The classification rule of MATH_V1 §5, applied to the measured rates, puts N5 in the element class and N6 in the time class (as predicted from N1 and N4); N5's condition failure is within max(3 pp, 30 %) of 1 − (1 − ε)^50; N6's failure for 300 reads is within 3 pp of its failure for one read |
| S2 | **Cross-node healing.** N1 at 95 % erasure; N3 supplies exact values for a random 30 % of the facts. The other 70 % are read ≥ 5 pp more accurately with those values known than without (soft joint reading, scenes 1020–1027) |
| S3 | **Primitive transfer.** DISAGREE (generated in ENGINE1) on N5, reading x by molecule counts twice: it flags N5's first-reading errors with recall ≥ 0.90 and precision ≥ 0.45 |
| S4 | **Zoom.** Theorem 1's bound holds (observed ≤ bound + 3 pp) at the fact level and node level on N1–N6, and at the sphere level for an operation reading one element from each of N1, N3, N5, delivered over N2 |
| S5 | **Protocol.** 2,000 envelopes between random node pairs over N2, tampered with p = 5 % per hop, receiver's book outdated with p = 5 %: 0 wrong adoptions; ≥ 99 % of legitimate envelopes delivered within 3 resends |
| S6 | **Law 0.** Injected envelopes (out-of-range value, unknown operator, replay): 100 % refused; 0 legitimate envelopes refused |
| S8 | **The theorem's exception.** On N7, condition and scan failure **exceed** the compounding bound (the corollary of Theorem 1); on every other node they do not exceed it by more than 3 pp |

Every prediction reported pass or fail; nothing changed after the run.
