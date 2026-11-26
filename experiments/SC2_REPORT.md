# SC2 report: the first predicted gap of the operation table (FLOW), with a control

Pre-registration: `PREREGISTRATION_SC2.md` and amendments 1–3, all public before the draw; tasks drawn from drand round
6654866 (08:30 UTC, 19 Nov 2026, verified); frozen predictor sha256 `0c976ed0…`; draw record public at 08:39 UTC before
any model call (RSOS-Language `36fc561`). Runs on the owner's machine, 19 Nov 2026, 08:50–12:18 UTC. Scored by
`sc2_analyse.py` and `sc2c_analyse.py`, both written before the draw → `results/sc2.json` (sha256
`b63e60e9…`), `results/sc2c.json` (sha256 `006429a6…`).

**Complete:** Mistral Large 4 on SC2 and SC2-C (both arms, 16 tasks each). **Incomplete:** Gemini 3.8 Flash; its prepaid
credit ran out during the runs (HTTP 402 "prepayment credits are depleted", `results/a7_errors_SC2*_gemini_38flash.jsonl`):
SC2 B2 13 of 16 tasks, X5b 0; SC2-C B2 16, X5b 4. Not scored; resumable with the same command once the credit is
topped up. Q9 (DeepSeek, GLM) not run.

## Strongest finding: the predicted property of the new operation held

Before FLOW existed, the operation table's law said one-call JSON Patch would fail **at least 5%** of requests of the
new kind (scan the state and compute a value per match), more than twice the hand-over rate, while RSOS blind
planning stays exact. Measured on Mistral Large 4: **JSON Patch failed 19 of 128 FLOW requests (14.8%)**, against 3.1%
on hand-overs and 0.4% on one-key operations in the same runs; **RSOS blind was exact on 16/16 tasks with FLOW**, an
operation learnt from one line of description, with 0.56 invalid operations per task (all rejected before running).
The frozen predictor's places held too: AUC 0.95 over all steps, and 4 of its 10 named steps failed, including its
first.

## Results (Mistral Large 4)

| Cell | Arm | Exact | Notes | Tokens per correct task | USD per correct task |
|---|---|---|---|---|---|
| SC2 (FLOW wording) | JSON Patch (B2) | 10/16 | 22 failed steps, 19 of them FLOW | 78,028 | $0.2668 |
| SC2 (FLOW wording) | **RSOS blind (X5b)** | **16/16** | 0 failed steps | **20,541 (0.26×)** | **$0.0658 (0.25×)** |
| SC2-C (objects named) | JSON Patch (B2) | 6/16 | 15 of 128 named-object requests failed (11.7%) | | |
| SC2-C (objects named) | RSOS blind (X5b) | **14/16** | 2 tasks: planner operations for long object lists (up to 19 objects) rejected three times, step not executed | | |

## Predictions

| ID | Prediction | Verdict |
|---|---|---|
| Q1 | RSOS blind exact on FLOW, 0 failed FLOW steps | **pass** (16/16) |
| Q2 | JSON Patch fails ≥ 5% of FLOW requests | **pass** (14.8%) |
| Q3 | ordering FLOW > hand-over > one-key | **pass** (14.8% > 3.1% > 0.4%) |
| Q4 | channel ≤ 0.1× on FLOW steps | **fail** (0.104×, known at the draw) |
| Q5 | ≤ 1 invalid RSOS operation per task | **pass** (0.56) |
| Q6 | failed steps within the frozen predictor's interval | **fail**: predicted 7.6 (interval 2–14), observed 22. The code underestimated; the sentence-law (Q2) was right |
| Q7 | predictor AUC ≥ 0.8 and a failure in its top 10 | **pass** (AUC 0.95; top-10 steps that failed: ranks 1, 5, 6 and 10) |
| Q8 | ≥ 50% of wrong keys out of date | **pass** (61%) |
| Q9 | DeepSeek, GLM | not run |
| Q10 | JSON Patch fails ≥ 2× more often when it must find the objects | **fail**: 14.8% vs 11.7% (1.27×) |
| Q11 | RSOS blind exact on the control | **fail**: 14/16 |

## What the misses show

- **Q10: finding the objects is not the main cause.** With every object named, JSON Patch still failed 11.7% of the
  same requests. What makes these requests hard for a one-call planner is producing a correct value for many objects
  at once from a state that has changed since the start, whether it has to find them or is told which they are. The
  law's ordering and the new operation's property held; its stated cause was too narrow. The operation table's first
  axis (what an operation reads) stands; the explanation is corrected to "how many values the planner must produce
  from changed state".
- **Q11: the first RSOS blind task failures on record.** On the control, the RSOS planner had to write one operation
  per named object (up to 19 per request); on two tasks its operations were rejected three times (38 and 3 invalid
  operations), the step was not executed, and later steps reading those values ended wrong. No value was written
  wrongly in silence: every failure is a step the runtime refused. With FLOW (one line for the same change) the same
  model was exact on 16/16. The operation is what made the blind planner reliable on these requests.
- **Q6: the frozen code underestimated.** It had never seen an operation that computes per match and treated FLOW like
  a hand-over; the sentence-law predicted the compounding. The code's places were right (Q7); its count was not.

## Diagnosis from the transcripts (added 19 Nov, 18:58 UTC; verdicts unchanged)

`results/a7_transcripts_SC2C_mistral_large40.jsonl` shows three causes behind the two RSOS failures on the control:

1. **The output cap of the run (16,000 tokens per call, fixed for every arm in A8 amendment 4).** Mistral Large 4 spent
   up to 15,999 of them thinking; the reply came back empty or cut mid-line (`INHERIT lamp.x`). Both failed RSOS tasks
   hit the cap. It also touched **9 of JSON Patch's 10 failed control tasks** (and 3 of its 6 failed SC2 tasks); RSOS
   with FLOW never reached it on SC2. The cap therefore also confounds Q10: on the control, truncation and "finding the
   objects" cannot be separated.
2. **A wrong error message in the harness's FLOW extension** (`experiments/sc2_tasks.py`, written for SC2). When the
   planner wrote `FLOW y OVER name crate,bin,…`, it was told "unknown field in 'y'" instead of "unknown field 'name'".
   The refusal was right; the feedback pointed at the wrong field, so the retries could not correct it.
3. **The planner's own RSOS errors:** FLOW over a list of names (FLOW selects by a field such as `owner`), `FUSE lamp.x
   lamp.x 2` (FUSE adds two keys, not a number), `INHERIT … 500` without `+`. The runtime refused every one.

The pre-registered verdicts stand (Q10 and Q11 fail). A new pre-registered control, **SC2-C2**, will rerun the control
with the error message corrected and no output cap below the model's maximum, before any claim about the cause.

## SC1 P7 (from the same session)

BPE (o200k) on the owner's machine: RSOS program + digest **0.548×** the tokens of JSON Patch + digest over all SC1
steps (≤ 0.6×: pass), and larger on conditional steps (1,003 vs 984 tokens: pass). **P7 passes**; SC1 is P1–P7 pass,
with P4 missed on Gemini.

## Totals

RSOS blind planning across all complete cells: **318 of 320 tasks exact** (A7, A8, SC1, SC2, SC2-C); the 2 failures are
on SC2-C, steps refused by the runtime, none silent.

## Artefacts (sha256)

    results/a7_results_SC2_mistral_large40.jsonl
    results/a7_results_SC2C_mistral_large40.jsonl
    results/a7_results_SC2_gemini_38flash.jsonl       (incomplete)
    results/a7_results_SC2C_gemini_38flash.jsonl      (incomplete)
    results/a7_errors_SC2_gemini_38flash.jsonl, results/a7_errors_SC2C_gemini_38flash.jsonl

Hashes in `results/SC2_HASHES.txt`. Transcripts on the run machine, added on upload.
