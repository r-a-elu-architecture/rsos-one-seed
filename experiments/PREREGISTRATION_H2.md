# H2 pre-registration: the landing changes the place, travels inward, and the lack speeds it up

Written before the run. Owner's words (17 Nov, verbatim in `corpus/chat-4/owner_turns_17nov.md`): the particle
"becomes part of it like … water … trough skin then capilairs then cell it will have the effect on the cell"; "if a
person … dont drink the water for 4 days the body will react fully … the signal will go through the organs and
processes much faster since it was for a long time without that". Understanding v2, rows 11–12.

## Model (`experiments/h2_inward.py`)

200 nodes, each with three depths (surface → capillary → cell) and a reserve at the cell that each node consumes at
its own rate (log-normal, mean 0.05 per step; unknown to outsiders). A node works while its reserve is above 0.
Dryness = steps since anything last reached its cell. Each step, K = 10 particles land; a particle changes the node
it lands on (no new node) and travels inward one depth at a time.

- Speed rule (owner): crossing one depth takes τ = max(1, round(3 / (1 + d/10))) steps, d = dryness at landing.
  Ablation: constant τ = 3.
- Size rule (owner): at the cell the particle adds 1 × (1 + min(d, 20)/20) to the reserve (cap 3).

Policies (same budget):

| Policy | Where particles land |
|---|---|
| R | at random |
| G guess | greatest lack estimated from outside: steps since this policy last supplied the node × mean consumption |
| G report | greatest lack reported by the host itself (its own reserve; dryness breaks ties) |

300 steps, 20 seeds.

## Predictions

- P1: working share: G report ≥ G guess + 0.05 and ≥ R + 0.10 (speed rule on).
- P2: the advantage of G report over R is larger with the speed rule than with constant speed (by ≥ 0.02).
- P3: G report keeps the long-dry share (nodes dry for > 30 steps) ≤ 2%.
