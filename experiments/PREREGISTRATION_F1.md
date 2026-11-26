# F1 pre-registration: feedback (the cybernetic loop) in the White Dragon engine

Written before the run. Owner (17 Nov, verbatim): "in the sub balls happens the same"; the engine "grows
exponentially". Step 3 of the plan approved with "go" (10:09): children change their parents and the node.

## Model (`experiments/f1_feedback.py`, on `rsoslang.dragon`, 48 metric balls, 8 domain books × 6 measures)

Six generations, budget k = 4 paths per frontier ball, frontier capped at 300 balls (random sample). A child is
**useful** when it passes `heal_filter` (measurable, new, good intention) and its deficit is lower than its parent's.

| Loop | How paths are chosen | What children do afterwards |
|---|---|---|
| Open | k paths at random among the golden-light paths | nothing |
| Feedback | k paths sampled in proportion to the entry's weight | useful child: its entry's weight × 1.25, and the parent (and up the chain to the root ball) takes the child's lower deficit and its measures; filtered-out child: entry weight × 0.8 |

10 seeds (300–309).

## Predictions

- P1: useful share of children over generations 2–6: feedback ≥ open + 0.10.
- P2: steadiness: coefficient of variation of the useful count over generations 2–6: feedback ≤ open.
- P3: root balls: mean deficit of the 48 roots after 6 generations falls by ≥ 0.10 under feedback (open loop
  leaves them unchanged by construction).
- P4 (guard against collapse): domains used in generation 6: feedback ≥ 6 of 8.
