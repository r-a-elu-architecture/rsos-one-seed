# A4 pre-registration: does latent drift become wrong answers?

Written before any A4 code or run (17 Nov 2026). Brief: `BRIEF_A4_LATENT.md`. Branch `claude/a4-latent` (parallel
rule: merged to `main` only at the end, after a rebase). Files: harness `experiments/a4_latent.py` (new; imports
`a1_agents.py`, `a3b_hologram.py` and `a3b_hdragon.py` unchanged and wraps them), analysis
`experiments/a4_analyse.py`. Results: `results/a4_latent.json` (saved with `common.save`, hash in the report), runs
`results/a4_results.jsonl` + `results/a4_runs.json`, every message and LLM call `results/a4_transcripts.jsonl`,
replay check `results/a4_replay_check.json`. Smoke runs only on seed 999 (`results/a4_smoke_transcripts.jsonl`).

## Why

A3: D (Slipstream-style anchors) reached 16/16 exact successes with 40 of 48 corruptions still in the worker's
replica (0/16 replica-consistent), because the planner resolved every value from its own correct copy and no agent
ever computed from the worker's copy. A4 removes that protection on some steps: the worker must compute the new
value from its own copy. The question is whether latent drift then becomes wrong authoritative results.

## Frozen files and replay check (before any live call)

`a1_agents.py`, `a3_run.py`, `a3b_hologram.py`, `a3b_hdragon.py` are not edited (checked with `git diff` against the
branch base in the analysis). A4 replaces only, at run time and inside the A4 process, three module attributes of
`a1_agents`: `make_task` (A4 generator), `drift_plan` (A4 drift plan) and `SYS["planner"]` (one added sentence,
below). Both run_task functions read these at call time, so all five conditions get exactly the same change.

Before any live call: (1) every recorded A3b H-dragon run (`results/a3b_transcripts_hd.jsonl`, 16 runs) is replayed
through the current `a3b_hologram.run_task` + `HDragon` (recorded outputs fed back, every prompt asserted identical)
and must reproduce its result record (success, line_acc, replica_success, final_errors, steps_failed, n_calls,
channel_tok, channel_bpe, channel_bytes, billed_tok, out_tok, drift); (2) `a3b_analyse.py`, run unchanged in a clean
worktree of the branch, must give results_sha256 `0ae0d0315ac392184128252c5d8b57eabfc9c977f10eb6e02b6f7eda20507120`.
Required: 0 mismatches and the same sha. If either fails, nothing is run live and the failure is reported.

## Host (unchanged from A3/A3b)

Planner → worker → checker, all `claude-haiku-5-5` (headless `claude -p`, no tools), same worker and checker
system prompts, same worker edit format, same checker prompt (request, instruction, diff of the decoded changes on
the checker's own copy) and verdict format, max 2 retries, 30-line state, 14 change requests, 3 drifts per task
injected into the worker's copy at steps 4, 8, 12 (48 per condition). **The checker is not given extra state:** it
sees only the diff, exactly as in A3, so it cannot recompute a derived value from its own copy.

**Planner prompt change (all conditions):** A3's planner system prompt plus one sentence: *"Exception: a request
that begins with 'Worker-computed:' reads values for which only the worker's state is authoritative. Do not look up,
compute or state any value for it: restate its operation word for word (without the prefix), and the worker
computes the result from its own state."*

## Tasks: seeds 400–415 (16 tasks, nothing tuned on them)

Initial 30-line state exactly as A3 (`random.Random(seed)`, 5 services × 6 fields). Then, with a separate generator
`random.Random(seed * 7 + 1)`:

- **Drift keys**: 3 distinct keys k1, k2, k3 from the initial state with field in {replicas, retries, timeout_ms,
  owner, region}, each with a wrong value w ≠ true (A3's `rand_value`). The drift keys are **frozen**: no step
  writes or deletes them. Drift plan: step 4 → (k1, w1), step 8 → (k2, w2), step 12 → (k3, w3), injected into the
  worker's copy as in A3 (P/H: the worker's book; D/E: the worker's replica; A: the state sent with that step).
- **Compute steps (8 of 14)**: the request begins `Worker-computed: `. Steps **4 and 6 read k1, 8 and 10 read k2,
  12 and 13 read k3** (drift-reading: 6 per task, 96 per condition; at the drift step itself and later). Steps **1
  and 2** read a non-drift key (clean computes: 2 per task, 32 per condition; the baseline of the worker's own
  compute accuracy).
- **Compute operations** (chosen by the generator; target t ≠ source; t present, not a drift key, not a target of
  another compute; after its compute step t is frozen, so the derived value reaches the final state unchanged):
  - copy: `Make <t> equal to <s>.` (same field; any computable field);
  - add (replicas, retries): `Set <t> to <s> plus <d>, capped at 9.` d ∈ {1, 2}; timeout_ms:
    `Set <t> to <s> plus 500.`;
  - sum (replicas, retries): `Set <t> to <s> + <s2>, capped at 9.` (s2 a non-drift key of the same field);
  - cross-reference (region, owner): `If <s> is <x>, set <svc>.log_level to <l1>; otherwise set it to <l2>.` with x
    drawn from {true value, wrong value} so the wording does not reveal the branch.
  Every drift-reading compute is constructed so that the value derived from the drifted source **differs** from the
  true one and the true result differs from t's current value (a no-op change is never requested).
- **Normal steps (0, 3, 5, 7, 9, 11)**: A3's request kinds (set, inc, double, owner transfer, add, delete, cond,
  copy), resolved by the planner as in A3, restricted to non-frozen keys (an owner transfer is only drawn for an
  owner held by no frozen key; otherwise a set).

## Conditions (all live, fresh, on seeds 400–415; 80 task runs)

| | Protocol |
|---|---|
| **H-dragon** | A3b's hologram codec (`a3b_hdragon.HDragon`) in `a3b_hologram.run_task`, unchanged |
| **P** palace | A1/A3 P in `a1_agents.run_task`, unchanged |
| **D** anchors, Slipstream-style | A3 D, unchanged |
| **E** deltas, ACCP-style | A3 E, unchanged |
| **A** JSON full state | A1/A3 A, unchanged |

## Measures (all from the run records and transcripts)

- **Exact success**: authoritative final state (planner's copy; A: approved state) = ground truth.
  **Replica-consistent success**: every copy = ground truth. Wrong final lines.
- **Per compute step** (target t is frozen afterwards, so the authoritative final value of t is its value after the
  step): *correct* (= f(true sources)); **traced to drift** (= f(sources with the drifted value), drift-reading
  steps only); *other wrong* (any other value, or unchanged after a failed step). Reported per condition, split into
  same-step (4, 8, 12) and later (6, 10, 13) and clean (1, 2).
- **Planner leak** (compute steps): the instruction states the resolved value (the true f token appears in the
  instruction and not in the request; for a cross-reference, the instruction names exactly one of l1, l2). Reported;
  a leaked step is still counted in every measure.
- Channel tokens per task (regex proxy `\w+|[^\w\s]`, as A1–A3b) with the BPE guard (tiktoken o200k_base, required)
  and bytes, per edge; billed LLM tokens, calls, wall-clock; drift healed / healed with 0 model calls / left in any
  copy; steps failed.

## Predictions (from the brief, fixed now)

| | Prediction | Pass condition |
|---|---|---|
| **L1** | Latent drift turns into wrong results: D's exact successes fall below its A3 level | D exact ≤ 12/16 |
| **L2** | The integrity protocols are unaffected | H-dragon ≥ 15/16 exact **and** 16/16 replica-consistent; P the same (both must hold) |
| **L3** | Wrong derived values are traced to injected drift in D, never in H-dragon | traced-to-drift count: D ≥ 10 and H-dragon = 0 |
| **L4** | The hologram stays at least as compact as the tent | H-dragon channel tokens per task ≤ D's, regex **and** BPE |

E and A are reported without a prediction.

## Rules

- Smoke runs only on seed 999 (not in the test set). If the smoke shows a harness bug or a planner leak rate above
  half of the compute steps, the fix is written as an amendment in this file and committed **before** the main run;
  no change after the main run starts.
- Resumable runner: each finished task appends its result and transcript at once; on a stop (usage limit) the runner
  is restarted, finished runs are loaded, runs with a transcript but no record are rebuilt by exact replay (as A3),
  and only the missing runs go live.
- The report gives every number from `results/a4_latent.json`, passes and failures alike.

## Amendment 1 (17 Nov 2026, after the seed-999 smoke, before the main run)

Smoke (seed 999, D and H-dragon; `results/a4_smoke_transcripts.jsonl`): the planner leaked 0 of 8 compute steps in
both arms (it restated every operation word for word). But all 8 compute steps failed in both arms (D 8, H-dragon 9
failed steps; identical final states), and the cause was the harness: the worker computed correctly (e.g.
`SET billing.owner = emeka` = gateway.owner), but the checker, which sees only the diff, rejected each one:
*"the checker has no gateway.owner value to confirm that emeka is the correct target. Equality cannot be verified."*
That makes a compute step impossible in every condition, so it cannot test latent drift.

**Fix (all conditions):** A3's checker system prompt plus one sentence, applied in the A4 process like the planner
sentence (a fourth attribute, `SYS["checker"]`): *"For a request that begins with 'Worker-computed:', the worker's
state is authoritative for the values it reads: verify that exactly the named target key changed and nothing else,
and do not reject because you cannot see the source values."* The checker still sees only the diff (no extra
state), as registered. Nothing else changes. The smoke is repeated on seed 999 to confirm, and then the main run starts.
