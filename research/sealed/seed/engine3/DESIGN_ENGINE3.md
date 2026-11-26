# ENGINE3 design: the SCORE × TOTE engine on real LLM agents (for the owner's machine)

Written 20 Nov 2026, ~07:55 Vilnius. Private. A design, not yet the sealed pre-registration: the predictions are
sealed (hash committed) immediately before the first live call, with the beacon draw for the tasks.

## SCORE

| | |
|---|---|
| S | JSON Patch agents fail on whole-state requests: reassign_where 2.31 % (A7/A8), derive_where (FLOW) 14.8 % of requests (SC2, Mistral); failures concentrate on stale values and long scans |
| C (named before the run) | ① the model must read every matching key itself (read scope); ② values it read earlier go stale within the same plan; ③ the output grows with the number of matches and hits the cap (FAILURES_MAP #51) |
| O | JSON Patch failure on the whole-state families halved on a sealed, beacon-drawn task set; RSOS blind stays exact |
| R (primitives the engine may compose, all from the seed) | READY at the receiver (the agent's patch is checked against the state before it is applied); DISAGREE (two independent patch drafts; a step is flagged where they differ); ISOLATE (a flagged step is held and re-planned alone); a structural hint (the operation table row of the request) |
| E | failure per request family, cost per correct task, sealed |

## TOTE

Test (run a calibration slice) → Operate (the engine composes one guard from R) → Test → Exit when O is met on
calibration, or after 6 guards without improvement. The champion guard is then run once on the hold-out slice.

## Runs (owner's machine, hidden key input)

- Models: Mistral Large 4 (credits available), Gemini 3.8 Flash after top-up.
- Calibration: 8 tasks per family from the existing StateBench sets; hold-out: 16 beacon-drawn SC tasks.
- Harness: `a7_run.py` with a new guard hook; nothing in the frozen arms changes.

## Predictions (to be sealed before the first call)

1. A generated guard halves JSON Patch failure on whole-state families on the hold-out.
2. Attribution: removing the guard's primitive restores at least half of the failures.
3. Cost per correct task of the guarded JSON Patch agent stays above RSOS blind (blind remains cheaper).
