# F1b pre-registration: the feedback loop scored fairly

Written before the run. F1 scored usefulness against the parent's healed (moving) deficit, which penalised the
loop for succeeding, and the frontier cap hid steadiness.

## Changes from F1

- A child is useful when it passes `heal_filter` and its deficit is below its parent's **original** deficit
  (computed from the parent's relations, never updated).
- No frontier cap; instead a compute budget of 1,200 landings per generation, drawn from the whole frontier
  (ball uniformly, then path: at random in the open loop, by entry weight in feedback loops).
- Three loops: open, weights only, weights + parent healing. 6 generations, 10 seeds (700–709).

## Predictions

- P1: useful share, gens 2–6: weights + parent healing ≥ open + 0.05.
- P2: weights only ≥ open + 0.03.
- P3: CV of the useful count over gens 2–6: both feedback loops ≤ open.
- P4: root balls' mean deficit drop under weights + parent healing ≥ 0.10.
