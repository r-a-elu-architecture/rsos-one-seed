# ENGINE2: SCORE × TOTE engine; named causes grow new primitives; relations move the information limit (layer 2)

Written 20 Nov 2026, ~06:45 Vilnius. Private. Sealed before any ENGINE2 code. Follows ENGINE1 (`../engine/`).
New hold-out scenes **950–957** (ENGINE1's hold-out 940–947 is not reused). Calibration 800–803; Bear replication
804–807.

## SCORE for each target (causes named before the run)

| | T1 LAND, 10 % silent flips | T2 reading at 90 % erasure |
|---|---|---|
| S | recall 0.313 at precision 1.000 | 55.9 % |
| C | ① each bit judged alone; ② one fixed margin; ③ some flips undetectable (information limit) | ① hard per-fact decisions lock early errors in; ② fixed noise estimate; ③ near the information limit |
| O | hold-out recall ≥ incumbent + 0.10, precision ≥ 0.99 | hold-out ≥ incumbent + 2 pp |
| R (new primitives grown for C) | **tiered landing** (margin falls by a factor per round, up to 4 rounds; for ① ②); **soft reconstruction** (expected bindings from candidate probabilities; for ①) | **soft joint reading**: every fact keeps probabilities over its candidates; each pass cancels the expected contribution of all others and uses their uncertainty (for ①); **temperature** and **annealed σ** (for ②) |
| E | sealed hold-out | sealed hold-out |

## TOTE and the engine

- Each target: test → operate (children propose) → test; **exit** when the calibration score reaches incumbent +
  margin (then challenge on the hold-out), or after 8 candidates in a row without improvement, or at 40 candidates.
- Children as in ENGINE1 (Tiger, Lion, Leopard, Dragon, White Dragon explore; RSIA's causes tell Tiger and Dragon to
  include the new primitives in at least half of their proposals).
- **Father fixed:** Bear has its own budget (6 replications per target) and is outside Father's allocation.
- Root Genome hash-chained; Law 0 before every candidate.

## T4: transfer of the generated operator (no search)

DISAGREE (ENGINE1 champion: flag where plain and relational readings differ), unchanged, on scenes 960–967 under
three damages it never saw: 10 % silent flips, 30 % erasure, 70 % erasure.

## T5: a world with relations

Scenes 1000–1015 drawn from a fixed network: owner uniform; room given owner (the owner's room with p = 0.8);
surface given room (p = 0.8); height given surface (a band of 10 values, p = 0.8); x and y given room (the room's
region of 5 values, p = 0.8). Same fields and candidate values as before. The network is known to both sides.

Readers of the same damaged hologram (store as LivNR): **H** hard relational reading (incumbent, R5); **S** soft joint
reading, no relations; **SR** soft joint reading **with** the relations (mean-field over each object's facts).
Opponent: **CC** classic code **with compression** under the same network, idealised in its favour: it recovers
everything whenever surviving bits ≥ the ideal compressed length + 20, otherwise it falls back to the network's most
likely guess. Also CU, the uncompressed classic code (1,050 bits). Loss 85, 90, 95, 98 %.

## Predictions

| # | Prediction |
|---|---|
| G1 | At least one of T1, T2 promoted on the hold-out |
| G2 | Attribution: on each promoted target, switching the new primitive off removes at least half of the hold-out gain |
| G3 | T4: DISAGREE keeps precision ≥ 0.90 and recall ≥ 0.90 under all three new damages |
| G4 | TOTE: no candidate is evaluated after a target's exit |
| G5 | Father: explorers receive ≥ 60 % of the evaluations of each target |
| G6 | Root Genome chain verifies; Law 0: all out-of-range refused, none in range refused |
| Z1 | T5: SR ≥ S + 10 pp at 95 % |
| Z2 | T5: SR > CC at 95 % and at 98 % |
| Z3 | T5: CC = 100 % at 85 % (today's method wins inside its threshold) |
| Z4 | T5: S ≥ H at 90 % (soft joint reading helps without relations) |

Every prediction reported pass or fail; nothing changed after the run.
