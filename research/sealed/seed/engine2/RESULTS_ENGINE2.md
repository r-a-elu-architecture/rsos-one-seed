# ENGINE2 results (layer 2), private

Predictions: `PREREG_ENGINE2.md` (sha256 `a641004c…71f29`, commit 36f950b). Code: `engine2.py` (commit 6c33a45;
smoke test on non-test scene 700 only). Data: `RESULTS_ENGINE2.json`, `ROOT_GENOME_2.jsonl`. Run 20 Nov 2026,
~07:00 Vilnius; code unchanged during the run.

## Strongest finding

**Naming the cause (SCORE's C) moved both targets that parameter tuning could not.** In ENGINE1 the engine searched
45 candidates per target and moved LAND by +0.013 recall and the 90 % reading by +0.6 pp. In ENGINE2, with the causes
named and their primitives grown, both targets reached their goal within the first candidates and held on new
hold-out scenes:

| Target | Incumbent (hold-out) | Generated (hold-out) | Primitive grown for the named cause | Without that primitive |
|---|---|---|---|---|
| LAND, 10 % silent flips | recall 0.310, precision 1.000 | **recall 0.539, precision 1.000** | tiered landing (cause ②: one fixed margin) | 0.112 |
| Reading at 90 % erasure | 55.25 % | **59.33 %** | soft joint reading (cause ①: hard decisions lock errors in) | 53.67 % |

And **relations move the reading** (T5): with the world's relations, the same damaged store reads 86.9 % instead of
74.8 % at 85 % erasure, and beyond today's method's cliff (95 % erasure) 48.5 % against 15.6 %.

## T5: a world with relations (exact %)

| Erasure | H hard | S soft | **SR soft + relations** | CC classic + compression (idealised) | CU classic |
|---|---|---|---|---|---|
| 85 % | 70.81 | 74.75 | **86.88** | 100 | 100 |
| 90 % | 54.60 | 57.81 | **66.90** | 100 | 15.60 |
| 95 % | 38.54 | 41.85 | **48.46** | 15.60 | 15.60 |
| 98 % | 25.44 | 28.67 | **31.29** | 15.60 | 15.60 |

Compressed length under the relations: 748.5 bits on average (against 1,050 uncompressed).

## T4: transfer of the generated operator (DISAGREE)

| Damage (never seen) | Precision | Recall |
|---|---|---|
| 10 % silent flips | 1.000 | 1.000 |
| 30 % erasure | 1.000 | 1.000 |
| 70 % erasure | 0.994 | **0.836** |

## Predictions: 8 pass, 2 fail

| # | Result | Measured |
|---|---|---|
| G1 at least one of T1, T2 promoted | **pass** | both promoted |
| G2 attribution (ablation removes ≥ half the gain) | **pass** | T1: 186 % of the gain removed; T2: 139 % (without the primitive, the tuned candidate falls below the incumbent) |
| G3 DISAGREE ≥ 0.90 / 0.90 under all three damages | **fail** | recall 0.836 at 70 % erasure (1.000 / 1.000 at flips and at 30 %) |
| G4 nothing evaluated after a TOTE exit | **pass** | 0 |
| G5 explorers ≥ 60 % of evaluations | **pass (trivially)** | both targets exited on "target met" after 1 and 3 candidates; Bear never ran |
| G6 genome chain and Law 0 | **pass** | 10 entries, chain verifies; 1 / 1 out-of-range refused, 0 in-range refused |
| Z1 SR ≥ S + 10 pp at 95 % | **fail** | +6.6 pp (48.46 vs 41.85); +12.1 at 85 %, +9.1 at 90 % |
| Z2 SR > CC at 95 % and 98 % | **pass** | 48.46 vs 15.60; 31.29 vs 15.60 |
| Z3 CC = 100 % at 85 % | **pass** | today's method wins inside its threshold |
| Z4 S ≥ H at 90 % | **pass** | 57.81 vs 54.60 |

## Diagnosis

1. The engine's search machinery was hardly needed: once the cause was named, the first candidates carrying its
   primitive met the target (TOTE exited). The gain belongs to SCORE's C channel, not to Father or the children;
   G5 passed without being tested. Bear did not replicate the champions; the new hold-out confirmed them.
2. Relations help most where some information survives (+12 pp at 85 %) and less as it vanishes (+2.6 at 98 %).
3. Inside its threshold the compressed classic code still wins (100 % at 85–90 %); it was idealised in its favour.
   Beyond it, the seed reads three times more than it.
4. DISAGREE transfers exactly while the relational reading is reliable (flips, 30 %); at 70 % it misses errors that
   both readings share.
