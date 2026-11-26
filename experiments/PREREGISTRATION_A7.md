# Pre-registration A7: RSOS against the market's most efficient setup (M\*), blind planning, and the decoupling grid

Written 18 Nov 2026, before any A7 model call. Code: `experiments/a7_arms.py`, `a7_run.py`, `a7_analyse.py`
(committed with this file). Results: `results/a7_*`. Cost to the owner: **$0** (runs on the owner's Claude plan through
the A5 call, `claude -p`; A7c on a local model). Sources: pass 6–9 landings (`corpus/dragon_landings/`, sealed).

## 1. Why

A5 measured RSOS's assembly line (X5) against B1, which is RSOS's own per-step protocol (H-dragon), not the market's
best. A4's anchor arm had no hash check. No arm wrote a one-call JSON plan. A7 builds the missing denominator, **M\***,
and asks the question the prior art leaves open: **when the model names keys and a runtime computes every value, does
exactness stop depending on what the model must compute, and can the model plan without seeing any value?**

## 2. Stages

| Stage | Cells | Status of the code |
|---|---|---|
| **A7a** | B2 (M\*), X5r, X5b on A5's S1 and S2 seeds, default thinking | in this commit, replay-checked |
| **A7b** | the same arms with thinking off (`A7_THINK=off`); then dependency depth 1/4/16 and horizon 14/56/224 | thinking-off in this commit; the depth/horizon generator by amendment, committed and replay-checked before its runs |
| **A7c** | the size floor: the X5b planner on a local open model (Qwen2.5-0.5B, larger if the machine allows) against B2 on the same model | by amendment before its runs |

## 3. Arms (16 tasks per set each; one loop for all arms, `a7_arms.run_plan`)

- **B2, M\*:** one planner call writes the whole task as JSON Patch (RFC 6902), one patch per request, with literal
  values the model computes from the **full state it is shown**; then one audit call. This is the market's most
  efficient pattern for the same agents: one plan, structured edits, an audit.
- **X5r:** RSOS operations, exactly A5's X5 prompt (the planner sees the lines each request names).
- **X5b, blind:** RSOS operations; the planner sees **no state values**, only the requests.

**The same for every arm:** model Haiku 5.5, thinking setting, seeds, the A5 call with the Phase 0 fix (static first),
retries (`MAX_RETRY` 2), the runtime executing the plan on all three copies, the integrity layer (drift injected into
the worker copy at steps 4, 8, 12; green-dot check before every step; restore from the snapshot at 0 model calls), and
the **audit selection: one harness rule for all arms** (a step is audited if its request kind is state-dependent, or
its result is no change, or a seeded 1-in-4 sample). The request kind comes from the generator's templates and is
never shown to a planner. Only the representation of the plan and what the planner is shown differ.

## 4. Measures and cost

Exact task (final state equals the truth), replica-exact, line accuracy, steps wrong (approved but wrong), steps
failed, invalid outputs, calls, input, output and thinking tokens, wall time, drift healed at 0 calls. Cost: A5's
basis **api** (CLI scaffold removed, measured by null calls into `results/a7_scaffold.jsonl`; every remaining input
token at base price; output as measured) and **billed**, with A5's run-time price sheet. **Cost per correct task** =
total cost ÷ exact tasks. Paired bootstrap 95% CIs on cost ratios (10,000 resamples, seed 12345).

## 5. Predictions (A7a; each on S1 and S2)

| # | Prediction | Pass if |
|---|---|---|
| **P1** | The runtime beats M\* on exactness | X5r ≥ 15/16 on both sets **and** B2 ≤ 13/16 on at least one |
| **P2** | Blind planning costs no exactness | X5b ≥ X5r − 1 on each set |
| **P3** | Cost per correct task halves | X5b ≤ 0.5 × B2 (api) on each set |
| **P4** | Blind input halves | X5b input tokens per task ≤ 0.5 × B2 |
| **P5** | M\* must think more | B2 thinking tokens ≥ 2 × X5b |
| **P6** | M\*'s errors sit on state-dependent steps | ≥ 70% of B2's wrong or failed steps are INHERIT/FUSE/SCALE/ROUTE/REHOST kinds |
| **P7** | Sanity: one plan | every arm ≤ 3 calls per task |
| **P8** | Sanity: the shared layer heals | every arm heals every drift at 0 calls |

**REACH:** `REACH cost_tenfold ON a7 TARGET 10 AGAINST m_star MEASURE cost_per_correct_task LIMIT …`. The 10× is an
instrument, not a prediction: the analysis reports the measured distance (B2 ÷ X5b cost per correct task).

**A7b predictions (fixed now):** with thinking off for every arm, **P1b** B2 exact drops by ≥ 3 tasks on at least one
set while X5b drops by ≤ 1; **P3b** X5b cost per correct task ≤ 0.3 × B2. Depth/horizon (fixed now): **P9** at depth
16 or horizon 224, B2 exact ≤ 50% while X5b ≥ 90%; **P10** X5b input tokens grow with the number of requests only, not
with the state size.

**A7c predictions (fixed now):** **P11** X5b on the local model ≥ 12/16 exact on S1 where B2 on the same model ≤ 4/16.

**Failure is information.** If P1 fails (M\* ties), the claim becomes the pattern, not the notation. If P2 fails, the
planner needs values and the privacy property is not available. Every verdict is published.

## 6. Analysis

`python experiments/a7_analyse.py default` (and `off`) → `results/a7_<think>.json` with `results_sha256`. No model
calls. Error split by request kind is part of the table.

## 7. Procedure

1. `python experiments/a7_run.py replaycheck S1` and `S2` (0 calls): every arm with correct plans reaches the truth
   16/16, heals 48/48 at 0 calls, 0 invalid, identical audit selection across arms, no state value in X5b's prompt,
   A1–A5 harness files unchanged against `main`. **Passed on both sets at commit time**
   (`results/a7_replay_check_S*_default.json`).
2. Smoke: `python experiments/a7_run.py smoke S1` (seed 999, all arms). Code fixes found by the smoke are logged as
   amendments here before the live run; predictions do not change.
3. Live: `python experiments/a7_run.py run S1`, then `S2` (resumable). Then `A7_THINK=off` for A7b.
4. Analysis, report `experiments/A7_REPORT.md`, failure map, status.

## 8. Fairness notes (written before results)

- M\* sees the full state because it must: its values are literal. That is the pattern under test, not a handicap.
- No prefix in A7a reaches the 512-token cacheable minimum except B2's state on a retry round; the api basis prices
  all content at base input for every arm (as A5). A cache read on B2's retries would lower its cost by at most the
  retry share; the analysis reports retry calls per arm so the effect can be bounded.
- Batch pricing would scale every arm equally and does not change any ratio.
- The auditor of B2 sees the same request, result, sources and before-values as the RSOS arms; only the plan's
  notation differs.

**Amendment log (18 Nov 2026, after A7a, before any A7b verdict).** A7b thinking-off: the control does not take
effect (S1 off: thinking tokens 0 in 0/48 tasks; the CLI ignores `MAX_THINKING_TOKENS=0`, `alwaysThinkingEnabled:false`
and `--effort low` for `claude-haiku-5-5`). Cell stopped per the brief; S2 off and the `off` analysis not run. P1b and
P3b keep their wording and have no verdict until a working control is committed and replay-checked.

**Amendment log (18 Nov 2026, 13:20 Kyiv, before any A7c run).** A7c backend: `experiments/a7_local.py` (Ollama on the
owner's PC, `A7_BACKEND=ollama`). Model **qwen2.5:1.5b** ("larger if the machine allows": an i7-4510U, 16 GB RAM, no GPU;
1.5B is the largest that runs S1 in about two hours). Every arm and every call: temperature 0, seed 0, context 8192
tokens; cost 0; no CLI scaffold. Arms B2 and X5b on S1 (P11 is defined on S1); X5r and S2 only if time allows. The
harness, prompts, audit rule and integrity layer are unchanged; the local model is the auditor as well as the planner,
for both arms. P11 unchanged: X5b ≥ 12/16 exact on S1 where B2 on the same model ≤ 4/16. Results label `local_qwen15`.
Wiring checked against a stub server (calls, token counts and result files), 0 real model calls.

**Amendment log (18 Nov 2026, 13:40 Kyiv, before any A7b long-task run).** Generator `experiments/a7_tasks.py`
(A1/A4 request templates only; the harness, prompts, arms, audit rule and integrity layer unchanged). Cells, 16 seeds
each: **L1** 56 steps, chains of 4 dependent requests, 30 keys (seeds 500–515); **L2** 224 steps, chains of 16, 30 keys
(600–615); **L3** 56 steps, chains of 4, 300 keys / 50 services (700–715). Measured longest dependency chain per task
(reported, not targeted): L1 5–13, L2 29–73, L3 4–7. Drift: 3 events at n/4, n/2, 3n/4 on keys untouched afterwards,
skipped where none exists (L2: 47 of 48). Long plans: 15-minute timeout per call (A5: 3). Replay checks pass on L1–L3
(every arm 16/16 with correct plans, every drift healed at 0 calls, identical audit selection, no value in X5b's
prompt); the replay pass rule now compares healed drifts with the drifts generated instead of a fixed 48 (S1 and S2
still 48/48, pass). Operational verdicts, fixed now: **P9** on L2: B2 ≤ 8/16 exact and X5b ≥ 15/16. **P10**: X5b
input tokens per task on L3 ÷ L1 ≤ 1.5 while B2's ≥ 3. Analysis: `a7_analyse.py default L1,L2,L3` →
`results/a7_long_default.json`.

