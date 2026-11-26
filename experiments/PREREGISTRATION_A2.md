# A2 pre-registration: the knowing White Dragon on the A1 host (D84, U107)

Written after A1 and before any A2 run. Code: `experiments/a2_dragon.py` (transplant hooks in
`experiments/a1_agents.py`, `mods`, default off). Results: `results/a2_runs.json`, `results/a2_dragon.json`,
transcripts `results/a2_transcripts.jsonl`.

## Host

A1 condition **C (summaries + retrieval)**, the A1 configuration with the most room to improve (A1: drift reached
the final state, retrieval misses; P, A and B leave little error to remove). Decomposed into five parts with their
functions and the A1 measurements: **planner, worker, checker, memory, channel**. Agents: `claude-haiku-5-5` as
in A1. Task set: seeds 200–205 (6 tasks, same generator, same drift injection at steps 4, 8, 12).

## The transplant (executable)

A landing = part × depth × domain mechanism:
- **surface**: text added to the agent's system prompt;
- **procedure**: a procedure block inserted into every prompt the agent receives;
- **structure**: a graph change from a fixed menu: memory_journal, retrieval_k16 (memory); checker_full_view,
  second_checker (checker); worker_full_view (worker); planner_go_nogo (planner); readback (channel).
Memory and channel take only structure. Landings apply cumulatively in their order.

## Arms (same budget: 4 transplants each)

1. **Knowing dragon**: `claude-opus-5-5` receives the parts, their functions and measured A1 performance, a
   10-domain library (rocketry/mission control, immunology, chemistry, socio-technical safety, quantum error
   correction, control theory/cybernetics, genetics/proofreading, double-entry audit, mission command, ecology),
   the depths and the menu. It returns the ordered map: part, depth, domain, source mechanism, payload or
   primitive, predicted error reduction per task, predicted token change, dependencies.
2. **Blind**: random part, random valid depth, random domain (rng seed 300); payload written by the same model from
   part + depth + domain only, no performance data.
3. **Weighted (F1b)**: random part and depth; domain drawn by weights that start equal and add the measured gain of
   each landing.
4. **Shuffled order**: the knowing landings in a random non-identity order, prefixes 1–3 (prefix 4 = the same set).

Measured after every landing on the 6 tasks: wrong final lines per task (primary), exact successes, billed tokens,
drift caught. Gain of a landing = errors before − errors after.

## Predictions

- **Q1** total error reduction after 4 landings: knowing ≥ 2 × blind and knowing ≥ weighted.
- **Q2** knowing: measured gain > 0 for at least 3 of 4 landings.
- **Q3** calibration: knowing's predicted total reduction within ±50% of the measured total.
- **Q4** order: area under the error-reduction curve over landings 1–4, knowing map ≥ shuffled.

## Descriptive (no prediction)

Whether the knowing dragon independently chooses the palace mechanisms (per-line checksum + restore = green dot +
White Dragon heal) for the memory part, and from which domain.

## Limits fixed now

Six tasks per stage and stochastic agents: a stage-to-stage difference of < 0.5 wrong lines per task is within
noise (A1 smoke runs vary by about that). The menu of structures is ours, so the dragon chooses among them; it does
not invent new graph structures (it writes free text at surface and procedure depth).
