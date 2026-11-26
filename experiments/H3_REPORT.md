# H3 report: healing that evolves, and healing of connections

Pre-registration: `PREREGISTRATION_H3.md` (committed before the run). Results: `results/h3_evolve_links.json`,
sha256 06fb93f8f4028a41…. 10 seeds (100–109), 300 steps, 20 palaces × 30 books.

| Policy | Delivery | Final mean book quality | Quality slope (steps 100–300) |
|---|---|---|---|
| A restore, links not healed | 0.167 [0.159, 0.175] | −0.055 | −0.00019 |
| B restore + link heal | 1.000 | −0.075 | −0.00030 |
| C evolve + link heal | 1.000 | **+1.563** | **+0.0055** |

P1 pass (links healed: 0.17 → 1.00). P2 pass (C − B = +1.64 in quality, same delivery). P3 pass (B flat or
falling, C rising).

## What it shows

- **Healing connections matters more than healing books.** With books healed but links left to drift, 83% of
  messages die on the connection: link drift accumulates and nothing repairs it.
- **Restore-healing keeps the network working but lets it decay**: edits slightly degrade on average and restore
  copies the sender's version, good or bad. **Evolve-healing (keep the better of the two) turns every repair into
  a selection step**, so the same repair traffic lifts quality steadily. This is the owner's "heal → evolve,
  transform": the repair event is also the improvement event, at no extra messages.

## Limits (honest)

- Both effects are close to built in by the model: B delivers 1.00 because a healed link always works; C rises
  because it selects the maximum. The test confirms the mechanism runs and sizes it; it is not an independent
  discovery.
- Quality is known exactly in the simulation (with 0.02 measurement noise). In a real host, "better" needs a
  measurable test, which is the White Dragon's `heal_filter` (measurable, new, good intention). Next: tie C's
  comparison to that filter instead of a scalar.
