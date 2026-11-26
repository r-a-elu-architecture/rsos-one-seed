# H2: the landing changes the place, travels inward, and the lack speeds it up

Pre-registration: `experiments/PREREGISTRATION_H2.md`. Code: `experiments/h2_inward.py`. Result:
`results/h2_inward.json` (results_sha256 `bf76a086…`). 200 nodes, 10 particles per step, 300 steps, 20 seeds.

| Policy | Working share (speed rule) | Working share (constant speed) |
|---|---|---|
| Random landing | 0.909 | 0.900 |
| Greatest lack, guessed from outside | 0.965 | 0.947 |
| Greatest lack, reported by the host (as pre-registered) | **0.826** | **0.405** |
| *Post-hoc:* reported lack minus help already on the way | *0.998* | *0.996* |

| | Prediction | Result | |
|---|---|---|---|
| P1 | Report ≥ guess + 0.05 and ≥ random + 0.10 | 0.826 vs 0.965 and 0.909 | Fail |
| P2 | Speed rule widens report's advantage over random by ≥ 0.02 | −0.08 vs −0.50 | Pass (for the wrong reason, below) |
| P3 | Report keeps long-dry share ≤ 2% | 53% | Fail |

## What happened

The host reported its lack honestly, but the report ignored the particles **already travelling inward** to it.
Because a particle needs several steps to cross surface → capillary → cell, the driest hosts kept reporting
"dry" and kept receiving every new particle, while the rest starved: everyone rushed to the same dry spot. The
speed rule softened this (faster arrival, shorter rush), which is why P2 "passed".

**Post-hoc (not pre-registered):** when the host reports its lack **minus the help already on its way**, the
system works 99.8% of the time, against 96.5% for the outside guess and 90.9% for random landing. That is the
largest effect in any healing test so far. With this fix the speed rule barely matters (0.998 vs 0.996), because
the right hosts are reached early. (The long-dry measure turned out to be a poor one: a full host that needs
nothing also counts as dry.)

## Reading in the owner's terms

The dry cell must signal its thirst, and it must also know the water is already coming. Without the second part,
every drop goes to the same cell. With it, the whole body stays working. This needs a pre-registered re-run before
it counts.

## H2b: the post-hoc finding confirmed, pre-registered, on fresh seeds

`experiments/PREREGISTRATION_H2B.md`; `results/h2b_report_net.json` (results_sha256 `cf928261…`), seeds 900–919.

| Policy | Working (speed rule) | Working (constant) |
|---|---|---|
| Random | 0.909 | 0.899 |
| Guess from outside | 0.963 | 0.945 |
| **Host reports its lack minus help on the way** | **0.998** | **0.996** |

P1 (≥ guess + 0.02 and ≥ random + 0.05): pass. P2 (speed rule changes it by < 0.01): pass.
