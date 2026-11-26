# A4 report: does latent drift become wrong answers?

Pre-registration: `PREREGISTRATION_A4.md` (commit 1, before any code or run; amendment 1 after the seed-999 smoke,
before the main run). Harness `a4_latent.py` (wraps the frozen `a1_agents.py`, `a3b_hologram.py`, `a3b_hdragon.py`
unchanged), analysis `a4_analyse.py`. Results `results/a4_latent.json`, **results_sha256
`c2f41b8092bbda58eb168198f23bc499721c0ebbda0f998df933fc8a61538736`**; runs `results/a4_results.jsonl`,
`results/a4_runs.json`; every message and LLM call `results/a4_transcripts.jsonl`; replay check
`results/a4_replay_check.json`. Branch `claude/a4-latent`.

Host as A3/A3b: planner → worker → checker, all `claude-haiku-5-5`. 16 new tasks (seeds 400–415) × 5 conditions =
80 task runs, all live, 0 replayed, 4,000 LLM calls, $1.57. 8 of the 14 steps per task are **worker-computed**: the
worker must derive the value from its own copy. 6 of these per task read a drifted key, 96 per condition: 48 at the
drift step itself and 48 later. The other 2 per task are clean, 32 per condition.

## Strongest finding

**A3's latent drift was a delayed failure, not a harmless one. As soon as the worker computes from its own copy,
D (Slipstream-style anchors) goes from 16/16 exact in A3 to 0/16, and 93 of its 96 drift-reading computations
come out exactly equal to the value derived from the corrupted line.**

- **D:** 0/16 exact, 0/16 replica-consistent, 95 wrong final lines. Of the 96 drift-reading computes, **93 are
  traced to the injected drift**: 46/48 at the drift step and 47/48 up to five steps later. The corruption stayed
  in the replica and kept producing wrong answers. 1 was correct and 2 were wrong in other ways. On the 32 clean
  computes D was **32/32 correct**. The worker computes correctly; it computes from a false copy. The protocol saw
  nothing: 0/48 drifts healed, 46/48 still in a copy at the end, and only 3 steps failed. **The checker approved
  every one of the 93 wrong values**, because the checker sees only the diff.
- **H-dragon:** 15/16 exact. It healed 48/48 drifts with 0 model calls, left 0 drifts in any copy and traced
  **0** wrong values to drift. 95/96 drift-reading and 32/32 clean computes were correct. Its one error (seed 407,
  step 6) was an LLM error on a true copy: the worker's healed book held `auth.owner = chen`, and Haiku wrote
  `SET billing.owner = bruno`. Channel: **473 tokens per task, 0.58× D in regex and 0.55× D in BPE (575 vs 1,038)**.
  It is the most compact protocol in the test and the only one that is both compact and correct.
- **P:** 16/16 exact and 16/16 replica-consistent, 96/96 and 32/32 computes correct, 48/48 zero-call heals,
  1,835 channel tokens.

The A3 tie (P = D = 16/16 exact) is resolved: **integrity is what separates them once any agent computes from a
replica**. The compact protocol without a hash is no cheaper in practice: its savings are paid back in wrong answers.

## Results (means per task, 16 tasks per condition)

| | H-dragon | P · palace | D · anchors | E · deltas | A · JSON full state |
|---|---|---|---|---|---|
| Exact success | **15/16** | **16/16** | 0/16 | 1/16 | 1/16 |
| Replica-consistent success | 15/16 | **16/16** | 0/16 | 1/16 | 1/16 |
| Wrong final lines (sum) | 1 | **0** | 95 | 81 | 31 |
| Tasks with a drift-traced wrong value | **0** | **0** | 16 | 10 | 6 |
| Drift-reading computes: correct / traced / other wrong (of 96) | 95 / **0** / 1 | **96 / 0 / 0** | 1 / **93** / 2 | 39 / 14 / 43 | 65 / 7 / 24 |
| · at the drift step (of 48) | 48 / 0 / 0 | 48 / 0 / 0 | 0 / 46 / 2 | 15 / 7 / 26 | 17 / 7 / 24 |
| · later steps (of 48) | 47 / 0 / 1 | 48 / 0 / 0 | 1 / 47 / 0 | 24 / 7 / 17 | 48 / 0 / 0 |
| Clean computes correct (of 32) | 32 | 32 | 32 | 32 | 32 |
| Channel tokens, regex (95% CI) | **473** (445–508) | 1,835 (1,765–1,918) | 812 (760–870) | 2,173 (1,971–2,372) | 16,880 (16,655–17,104) |
| Channel tokens, BPE o200k | **575** | 2,231 | 1,038 | 2,374 | 13,736 |
| Channel bytes | **1,651** | 7,057 | 3,086 | 7,773 | 44,922 |
| LLM tokens billed | **79,901** | 80,939 | 84,338 | 130,202 | 124,188 |
| LLM calls | **42.4** | 42.8 | 44.0 | 67.4 | 53.5 |
| Wall-clock (s) | **181** | 186 | 195 | 312 | 268 |
| Steps failed after 2 retries (sum) | **0** | **0** | 3 | 82 | 31 |
| Drift healed with 0 model calls | **48/48** | **48/48** | 0/48 | 0/48 | 0/48 |
| Drift in any copy at the end | **0** | **0** | 46 | 15 | 0 |

**Per edge (regex / BPE tokens per task):**

| Edge | H-dragon | P | D | E | A |
|---|---|---|---|---|---|
| Instruction | 338 / 353 | 510 / 575 | 420 / 516 | 519 / 553 | 5,036 / 4,077 |
| Edits | 42 / 80 | 187 / 343 | 127 / 177 | 509 / 603 | 6,930 / 5,592 |
| Door | 30 / 31 | 842 / 777 | 145 / 178 | 1,011 / 1,056 | 464 / 441 |
| Forward (incl. H-dragon's `?` + edits on a miss) | 63 / 111 | 181 / 332 | 120 / 167 | 134 / 162 | 4,450 / 3,627 |
| Heal | 0 | 116 / 204 | — | — | — |

"Other wrong" in E and A means the step failed and the target kept its pre-step value: A 24/24, E 40/43. E's
delta cascade (A3) returns, and is worse with computes: 82 failed steps. A's checker sees the full state, so it
often rejects the drifted line at the drift step, but it cannot repair the worker's computation. 7 drifted values
still got through. Neither E nor A had a pre-registered prediction.

The H-dragon instruction edge is smaller than in A3b (338 vs 808 tokens per task): compute requests are short and
the planner restates them word for word. This is a property of the A4 task mix and is not comparable to A3b.

## Predictions

| | Prediction | Result | |
|---|---|---|---|
| L1 | D exact ≤ 12/16 | **0/16** (A3: 16/16) | **Pass** |
| L2 | H-dragon and P each ≥ 15/16 exact **and** 16/16 replica-consistent | P 16/16 · 16/16; H-dragon 15/16 · **15/16** | **Fail** (H-dragon replica 15 < 16) |
| L3 | traced to drift: D ≥ 10, H-dragon = 0 | D **93**, H-dragon **0** | **Pass** |
| L4 | H-dragon channel ≤ D, regex and BPE | 473 vs 812 (0.58×); BPE 575 vs 1,038 (0.55×) | **Pass** |

**L2 failed, and the cause is exact:** one worker LLM error on a correct copy (seed 407, step 6 above). The
H-dragon protocol kept every copy identical, so the wrong value is in all three, which is why replica-consistent
success is also 15. This is not drift: 0/48 drifts survived and 0 values were traced to drift. The registered
condition does not distinguish protocol errors from model errors, so the fail stands as registered. P, on the same
kind of tasks, had 0 such errors.

## Integrity of this run (reported failures and corrections)

- **Replay check before any live call (pass):** all 16 A3b H-dragon runs were replayed through the current code
  with 0 mismatches on success, line_acc, replica_success, final_errors, steps_failed, n_calls, channel_tok/bpe/bytes,
  billed_tok, out_tok and drift. The drift comparison excludes `recovery_sec`, a wall-clock field. `a3b_analyse.py`,
  run unchanged in a clean worktree, gave **`0ae0d031…`** (match). `git diff main` on the four frozen files is empty,
  checked again in the analysis.
- **Amendment 1 (before the main run).** In smoke 1 (seed 999) every compute step failed in both arms. The worker
  computed correctly, but the diff-only checker rejected every computed value as "cannot be verified". One sentence
  was added to the checker system prompt in all conditions: accept the worker's values for worker-computed requests,
  and verify only that the target changed and nothing else. The checker still sees only the diff. Smoke 2 confirmed
  the fix (H-dragon exact; D wrong exactly on the drift-reading targets). Both smoke transcripts are kept
  (`results/a4_smoke1_transcripts.jsonl`, `results/a4_smoke2_transcripts.jsonl`).
  **Consequence for reading L3:** the checker is blind to computed values by design. A checker that recomputed from
  its own copy could have caught D's errors; that variant was not run.
- **Analysis correction (after the first numbers, before the report).** The planner-leak detector read `warn.`
  (with the full stop) as a different token from `warn`. As a result it flagged every cross-reference compute
  (41 per arm, identical in every arm, which exposed the bug). Fixed by stripping sentence punctuation. After the
  fix: **0 leaks in all arms**. A direct check agrees: the planner restated the request word for word in 128/128
  (P, A), 127/128 (H-dragon, D) and 126/128 (E) compute steps. No other number changed. First-pass hash
  `49fadb96…`, final `c2f41b80…`.
- The run finished without interruption (80/80 live, 0 replayed).

## Limits

One model family (Haiku-class), 16 tasks. The task is built so that every drift-reading compute has a distinct
drifted answer, and the drift keys are never rewritten. D's 93/96 is therefore the mechanism's ceiling under a blind
checker, not a natural base rate. D and E are re-implementations from public descriptions, as in A3.

## Next discovery action

1. **A4b: checker with its own copy.** Let the checker recompute worker-computed values from its own replica. This
   tests whether D's error becomes a detected rejection (and then a retry loop, since D's worker cannot repair its
   copy) and what that costs against H-dragon's 0-call heal.
2. **Error source split for L2-type failures:** run H-dragon and P on the 128 compute steps 3× each, to measure the
   worker's pure model-error rate on true copies (1/128 for H-dragon here, 0/128 for P). Then a protocol claim can be
   separated from model noise.
