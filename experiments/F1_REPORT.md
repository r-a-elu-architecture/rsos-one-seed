# F1 report: feedback in the White Dragon engine

Pre-registration: `PREREGISTRATION_F1.md` (committed before the run). Results: `results/f1_feedback.json`, sha256
93f4c71046da5a26…. 10 seeds (300–309), 6 generations, k = 4, frontier cap 300.

| | Open loop | Feedback loop |
|---|---|---|
| Useful share, gens 2–6 | 0.245 | 0.126 |
| CV of useful count | 0.33 | 0.35 |
| Root balls: mean deficit drop | 0 | **0.23** |
| Domains in gen 6 | 8 | 8 |

P1 **fail** (feedback halves the useful share). P2 **fail** (not steadier). P3 pass (the 48 roots improve by 0.23).
P4 pass (no collapse).

## Diagnostic (post hoc, not pre-registered: `f1_diag.py`)

| Variant | Useful per try | Duplicate rate |
|---|---|---|
| Open | 0.244 | 0.275 |
| Weights only (entries that helped are chosen more) | **0.287** | 0.278 |
| Parent healing only (children lower the parent's deficit) | 0.123 | 0.275 |
| Both | 0.126 | 0.253 |

## What it shows

- **The two halves of the loop do opposite things.** Reinforcing the entries that helped raises the hit rate
  (+0.043, under the pre-registered +0.10). Healing the parent **raises the bar**: once a child has improved its
  parent, the siblings must beat the improved parent, so fewer count as useful. The node gets better (roots −0.23
  deficit) and the stream of "improvements" thins, which is what a converging system should do.
- So "useful share" was the wrong success measure for a loop that heals its parents: it penalises the loop for
  succeeding. The right pair is node improvement (P3) plus hit rate against the **original** parent.
- Steadier growth did not appear: the cap (300) dominates the counts from generation 3 on in both loops.

## Next (to pre-register, not run here)

F1b: hit rate measured against the original parent, weights-only vs both, and a frontier without a cap but with a
compute budget, to test steadiness where the cap does not hide it.
