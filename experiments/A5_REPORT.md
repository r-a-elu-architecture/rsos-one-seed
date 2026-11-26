# A5 report: the model bill against the market's best setup (18 Nov 2026)

Pre-registration `experiments/PREREGISTRATION_A5.md` (written before any arm code; amendments 1–3 and three code fixes
committed before the live runs, all from seed-999 smokes). Phase 0 `experiments/A5_PHASE0.md`. Numbers:
`results/a5_cost.json` (from `experiments/a5_analyse.py`, 0 model calls), raw `results/a5_results_S1.jsonl`,
`results/a5_results_S2.jsonl`, transcripts `results/a5_transcripts_S1.jsonl`, `results/a5_transcripts_S2.jsonl`.
Model `claude-haiku-5-5` for every call, default thinking. 192 live tasks (6 arms × 2 sets × 16 seeds).

## 1. Strongest finding: the assembly line (X5) is 2.8–5.8× cheaper than the honest market best, with 32/32 exact

When the planner writes RSOS operations, the operations never need the state: the runtime reads and computes every
value. So all 14 requests of a task can be translated **in one call** and audited **in one call**. Measured:

| | S1 B1 | S1 X5 | S2 B1 | S2 X5 |
|---|---|---|---|---|
| Exact / replica-consistent | 16 / 16 | **16 / 16** | 15 / 15 | **16 / 16** |
| Model calls per task | 43.1 | **2.4** | 42.1 | **2.2** |
| Cost per task, basis api (market best) | $0.004598 | **$0.001233** | $0.003815 | **$0.001352** |
| Ratio X5 / B1, api [95% CI, paired bootstrap] | | **0.268 [0.240, 0.300]** | | **0.354 [0.336, 0.374]** |
| Cost per task, basis billed (CLI) | $0.008093 | $0.001397 | $0.007246 | $0.001452 |
| Ratio, billed | | **0.173** | | **0.200** |
| Drift healed with 0 calls | 48 / 48 | 48 / 48 | 48 / 48 | 48 / 48 |
| S2 drift-traced wrong values | | | 0 | **0** |
| Wall-clock per task | 106 s | **12 s** | 99 s | **12 s** |

The ratios are identical under all three price sheets on basis api (both arms bill only base input and output there;
all three sheets have output = 5 × input). On basis billed they move by under 0.003.

**What is new.** A per-request agent pipeline needs one model round trip per request because every request reads state
that the previous one wrote. Once the model's output is a state-independent program (RSOS operations) and a
deterministic runtime executes it, the dependency moves from the model to the runtime. The whole task becomes one
program the model writes at once, and integrity (green dot, heal from snapshot, three copies re-derived) stays at 0
calls. That is pass 4's planet 5 ("assembly line") made executable. The cost per task stops scaling with the number
of steps: X5 used 2.2–2.4 calls for 14 steps, against B1's 42–43.

**What it is not.** It is not 10×. K1 is judged on X3, and X5 (secondary) also misses ≤ 0.1.

## 2. Predictions

| | Prediction | Result | Verdict |
|---|---|---|---|
| **K1** | X3 cost ≤ 0.1 × B1 (api, all sheets, both sets) | S1 **0.581** [0.529, 0.635], S2 **0.828** [0.770, 0.890]; billed 0.578 / 0.650 | **fail** |
| K1 (secondary X5) | X5 ≤ 0.1 × B1 | S1 0.268, S2 0.354; billed 0.173 / 0.200 | fail |
| **K2** | X1s calls ≤ 0.4 × B1 | S1 22.1 / 43.1 = **0.512**; S2 26.5 / 42.1 = **0.629** | **fail** |
| **K3** | X2 output ≤ 0.25 × B1 | S1 1,997 / 5,498 = **0.363**; S2 2,239 / 4,170 = **0.537** | **fail** |
| **K4** | X3 exact ≥ B1 − 1 and replica 16/16 | S1 15 vs 16, replica **15**/16; S2 15 vs 15, replica **15**/16 | **fail** (replica) |
| K4 (secondary X5) | same for X5 | S1 16/16 (B1 16), S2 16/16 (B1 15) | pass |
| **K5** | S2 X3 drift-traced = 0 | 0 (X5 0; B1 0) | **pass** |
| **K6** | offline B1 within ±25% of live | S1 $0.005214 vs $0.004598 (−11.8%); S2 $0.004206 vs $0.003815 (−9.3%) | **pass** |

## 3. All arms

| Set | Arm | Exact | Calls | Out tok (think) | Content in | api $/task | api ratio | billed ratio | Invalid ops | Wrong steps applied |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 | B1 | 16 | 43.1 | 5,498 (2,544) | 18,492 | 0.004598 | 1.000 | 1.000 | — | — |
| S1 | X1 | 15 | 32.3 | 5,563 (3,714) | 17,479 | 0.004529 | 0.985 | 0.877 | 1 | 0 |
| S1 | X1s | 16 | 22.1 | 4,059 (2,635) | 12,701 | 0.003300 | 0.718 | 0.325 | 0 | 0 |
| S1 | X2 | 15 | 25.6 | 1,997 (1,520) | 13,361 | 0.002335 | 0.508 | 0.463 | 2 | 0 |
| S1 | X3 | 15 | 26.2 | 2,767 (2,105) | 12,896 | 0.002673 | 0.581 | 0.578 | 8 | 0 |
| S1 | **X5** | **16** | **2.4** | 1,952 (1,683) | 2,567 | **0.001233** | **0.268** | **0.173** | 1 | 0 |
| S2 | B1 | 15 | 42.1 | 4,170 (2,314) | 17,300 | 0.003815 | 1.000 | 1.000 | — | — |
| S2 | X1 | 16 | 31.2 | 5,516 (4,348) | 20,042 | 0.004762 | 1.248 | 1.028 | 14 | 0 |
| S2 | X1s | 15 | 26.5 | 4,899 (3,845) | 17,747 | 0.004224 | 1.107 | 0.453 | 17 | **1** |
| S2 | X2 | 16 | 26.1 | 2,239 (1,846) | 15,040 | 0.002624 | 0.688 | 0.530 | 7 | 0 |
| S2 | X3 | 15 | 27.5 | 3,250 (2,636) | 15,333 | 0.003158 | 0.828 | 0.650 | 11 | 0 |
| S2 | **X5** | **16** | **2.2** | 2,100 (1,817) | 3,021 | **0.001352** | **0.354** | **0.200** | 1 | 0 |

Scaffold: 571 tokens per call, 12 null calls at the start and end of each set, identical every time. Drift: 48/48
healed with 0 model calls in every arm of both sets; 0 drifted values in any final copy.

## 4. Every failure and every audit miss

| Set | Arm | Seed | What happened | Source of the error |
|---|---|---|---|---|
| S1 | X1 | 304 | step 0: correct `SET search.owner chen` rejected 3× ("cannot verify the listed state is exhaustive") | auditor false reject |
| S1 | X2 | 103 | step 1: correct `INHERIT gateway.retries search.retries` rejected ("no: … the result is correct") | auditor false reject (contradictory verdict) |
| S1 | X3 | 105 | step 5: correct `DEL gateway.owner` rejected (read the palace line `- go (was chen)` as a cleared value) | auditor false reject (palace notation) |
| S2 | B1 | 400 | step 2 (clean compute): `search.log_level` = error, truth warn | B1 agents |
| S2 | X1s | 403 | step 2: planner resolved the sum itself, `SET search.retries 0` (truth 9); SET is not a risk class and the 1-in-4 sample skipped it | **audit miss, unsampled** (the only one in 192 tasks) |
| S2 | X3 | 403 | step 9: planner wrote `DEL auth.replicas` (ar) for "remove auth.region" (ag); auditor rejected 3× correctly; step left out | planner palace-code error, caught |

Across the five X arms, 1 wrong step was applied in 160 tasks (2,240 steps), and that step was unsampled. The other
failures are steps left out after rejections: 3 false rejects of correct operations, 1 correct reject of a wrong one.
The audit approved 0 wrong steps.

## 5. Where the money goes now (the hard truth)

1. **The market's own fix is the biggest single cut, and it belongs to B1.** The recorded A3b/A4 bill was dominated by
   a harness artifact: 1,349 tokens per call of session context, written to cache at the 1-hour rate and never read.
   Fixing it cuts 1.86–2.23× on the CLI and 3.1–4.1× on the API (Phase 0). The brief's "8× before routing" projection
   was made against the unfixed baseline; against the honest baseline, the best per-step arm (X2) gains 1.5–2.0× and the
   assembly line 2.8–3.7× (api).
2. **Per-step RSOS arms do not remove enough calls.** The audit rule selects 10–12 of 14 steps (most operations are
   risk-class), so X1s/X2/X3 still make 22–28 calls. Each X call carries the grammar in its static prompt (below the
   512-token cache minimum, so it is paid at full price every time), and the X planners think more than B1's planner
   (S2 X1 planner 3,454 thinking tokens vs B1 planner 886). X1 and X1s cost more than B1 on S2.
3. **After batching, thinking is the bill.** X5's api cost is 79% (S1) and 78% (S2) output tokens, and 86–87% of that
   output is thinking. Input is 2,567–3,021 tokens per task.
4. **X3's palace notation did not pay** at this scale: shorter state per call, but more invalid operations (8 and 11)
   and two of the three auditor errors trace to code reading (`ar`/`ag`, `- go`).

## 6. Tests that follow

- **A6 (pre-register now): thinking control, applied equally.** B1 and X5 at low effort (or thinking off), same seeds.
  Arithmetic counterfactual from these numbers, not a result: with thinking removed from both arms and everything
  else unchanged, X5/B1 would be about 0.12 (S1). Accuracy without thinking is unmeasured, and that is the test.
- **Audit by equality instead of a model call** (pass 4 planet 9): a second, independent planner translation compared
  operation by operation; the auditor is called only on disagreement. This would remove the auditor's thinking and
  its false rejects (3 of 6 failures here).
- **Risk class from the request's verbs, not only the operations:** the one audit miss was a compute the planner
  wrote as a literal `SET`.
- **Generality:** a second task family and a second model family before any claim beyond this harness.

## 7. Integrity of the run

Replay check before any live call (`results/a5_replay_check_S1.json`, `_S2.json`): 32/32 recorded H-dragon tasks
reproduce through A5's B1 wiring with 0 mismatches; frozen files unchanged against `origin/main`; the X runtime given
test-only oracle operations reaches the truth on 80/80 tasks per set, all arms. Smokes only on seed 999 (three rounds,
recorded in `results/a5_smoke_results.jsonl`). The X planner never saw a parser written for the task generator; the
oracle exists only in the replay check. Price table: `experiments/a5_prices.json` (platform.claude.com pricing page,
18 Nov 2026), cross-checked against the CLI's own cost on 30 calls (max difference 1.1e-19 USD). Batch pricing was not
applied: the pipelines are sequential (a ×0.5 sensitivity leaves every ratio unchanged).
