# A2 report: the knowing White Dragon on the A1 host

Pre-registration: `PREREGISTRATION_A2.md` (committed before the run). Code: `a2_dragon.py`, `a2_analyse.py`.
Results: `results/a2_dragon.json`, results_sha256 `8916f4decec95d6eeeec666bf35a707104763b7405fa177ab639e7513a2e0e70`;
raw `results/a2_runs.json` (includes the dragon's full prompt and map), transcripts `results/a2_transcripts.jsonl`;
3D map `results/A2_map.png`. Dragon `claude-opus-5-5` (one call, $0.055); agents `claude-haiku-5-5`. 96 task
runs, 5,687 real LLM calls, $2.79. Host: A1 condition C (summaries + retrieval), seeds 200–205.

## The knowing map (part × depth × order, dependencies)

| Order | Part | Depth | Domain → mechanism | Depends on | Predicted | Measured |
|---|---|---|---|---|---|---|
| 1 | memory | structure | DNA mismatch repair + double-entry reconciliation → `memory_journal` (per-line checksum, restore from the approved journal) | — | −2.90 | **−2.50** |
| 2 | worker | structure | mission command, common operating picture → `worker_full_view` | 1 | −0.70 | −0.50 |
| 3 | checker | structure | full-ledger audit → `checker_full_view` | 1, 2 | −0.40 | 0.00 |
| 4 | planner | procedure | commander's intent + surgical checklist → "KEY: old → new, keys that must not change, done-condition" | 1 | −0.25 | −0.67 |

Wrong final lines per task (baseline 5.83):

| Arm | L1 | L2 | L3 | L4 | Total reduction | Exact successes after L4 | Billed tokens/task after L4 |
|---|---|---|---|---|---|---|---|
| **Knowing** | 3.33 | 2.83 | 2.83 | **2.17** | **3.67** (−63%) | 2/6 | 113,870 (+20%) |
| Blind | 5.83 | 5.67 | 6.17 | 8.17 | −2.33 (worse) | 0/6 | 185,628 (+95%) |
| Weighted (F1b) | 4.67 | 6.00 | 6.33 | 3.33 | 2.50 | 1/6 | 163,237 (+72%) |
| Shuffled map order (3,0,1,2) | 6.67 | 3.33 | 2.83 | 2.17 | (same set) | — | — |

Drift caught (18 events per stage): knowing 18/18 from landing 1 on; blind 0/18 throughout; weighted 0/18 until
its 4th landing happened to be `memory_journal`, then 18/18.

## Predictions

| | Prediction | Result | |
|---|---|---|---|
| Q1 | knowing ≥ 2 × blind and ≥ weighted | 3.67 vs −2.33 and 2.50 | Pass |
| Q2 | knowing gain > 0 on ≥ 3 of 4 | +2.50, +0.50, 0.00, +0.67 | Pass |
| Q3 | predicted total within ±50% of measured | 4.25 vs 3.67 (16% over) | Pass |
| Q4 | map-order AUC ≥ shuffled | 12.17 vs 8.33 | Pass |

## Strongest finding

**Given only the host's parts, their measured weaknesses and a cross-domain library, the knowing dragon
independently re-derived the palace mechanism and put it first.** Its landing 1 for the memory part is the green
dot + White Dragon heal (per-line signal, restore the differing place from the approved book), sourced from DNA
mismatch repair and ledger reconciliation. Its predicted gain (−2.9) was close to measured (−2.5), and it alone
moved drift caught from 0/18 to 18/18. The weighted arm confirms that this is where the lever is: its error rate
only fell once its random draw landed the same primitive (+3.0 in one landing).

**Knowing where to land is what made the transplants pay off.** The same landing budget, sampled blind, made the
host worse (8.17 wrong lines, +95% tokens) by stacking checker and retrieval changes onto a memory that still
accepted silent corruption. The knowing map cut errors by 63% for +20% tokens, with an order of magnitude better
calibration than chance. Order matters as the map's dependency lines say: the planner procedure landed first (the
shuffled order) made things worse (+0.83); landed after the memory journal it helped (−0.67).

## Limits

Six tasks per stage, stochastic agents: differences under about 0.5 wrong lines per task are noise (landing 3's 0.00,
landing 2's −0.50). Structures come from our menu of seven, so the dragon chose among them; it wrote free text only
at surface and procedure depth. One dragon call, so the map's variance between calls is unmeasured. The blind and
weighted arms each have a single random draw (rng seed 300).
