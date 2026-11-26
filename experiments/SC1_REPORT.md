# SC1 report: a grounded robot scene, predicted in public and run

Pre-registration: `PREREGISTRATION_SC1.md`, public at 05:43 UTC on 19 Nov 2026 (RSOS-Language `b9c8fc8`), before any
model call. Runs on the owner's machine, 19 Nov 2026, 06:09–07:15 UTC: Gemini 3.8 Flash (`gemini-3.8-flash`) and Mistral
Large 4 (`mistral-large-4-0`), arms B2 (one-call JSON Patch) and X5b (RSOS blind), A8 settings, replay check passed on
the run machine before the runs. Scored by `sc1_analyse.py` (written before the runs) → `results/sc1.json`, sha256
`3ad4cbe35bd37df35ce17f8cfefb8a5bac4150d10958b6629bb7df6cf2c4da73`.

## Strongest finding: the named step broke

Before the run we named five hand-overs where one-call JSON Patch would fail. **Mistral Large 4 failed two of them:
task 913 step 53 ("Everything owned by arm is now owned by drone", 29 objects; first on the list) and task 913 step 49
("Everything owned by crane is now owned by rover", 20 objects; third).** Both stayed wrong after three attempts each.
RSOS blind planning ended exact on task 913 on both models. These steps had never been run on any model before.

## Results

| Model | Arm | Exact | Failed steps | Tokens per correct task | USD per correct task |
|---|---|---|---|---|---|
| Gemini 3.8 Flash | JSON Patch (B2) | 15/16 | 1: 906 step 45 (hand-over) | 12,921 | |
| Gemini 3.8 Flash | **RSOS blind (X5b)** | **16/16** | **0** | **7,918 (0.61×)** | |
| Mistral Large 4 | JSON Patch (B2) | 14/16 | 5: **913 steps 49, 53** (named hand-overs), 54, 55 (values copied from the changed state); 906 step 50 (hand-over) | 33,563 | $0.1116 |
| Mistral Large 4 | **RSOS blind (X5b)** | **16/16** | **0** | **17,593 (0.52×)** | **$0.0561 (0.50×)** |

Drift: 3 injected per task; 192 of 192 repaired with 0 model calls, every arm, both models.

## Predictions

| ID | Prediction | Verdict |
|---|---|---|
| P1 | RSOS blind exact 16/16 on every complete model | **pass** (32/32) |
| P2 | JSON Patch ≤ 15/16 on at least one model | **pass** (15/16 and 14/16) |
| P3 | every JSON Patch failure state-dependent; RSOS 0 failed steps | **pass** (4 hand-overs, 2 values copied from changed values) |
| P4 | JSON Patch fails at least one of five named hand-overs | **pass on Mistral** (913/53, 913/49); **missed on Gemini** (it failed 906/45 instead) |
| P5 | RSOS ≤ 0.7× per correct task | **pass** (tokens 0.61× and 0.52×; USD 0.50×) |
| P6 | every drift repaired with 0 model calls | **pass** (192/192) |
| P7 | channel ≤ 0.6× in BPE tokens, and RSOS larger on conditional steps | **pass** (o200k 0.548×; conditional steps 1,003 vs 984 tokens; `results/sc1_channel.json`, run on the owner's machine) |

## What did not go as predicted, and what it shows

- **Gemini broke outside the named list.** Task 906 step 45: "Everything owned by drone is now owned by rover", only 5
  objects. At the start of that task the drone held 10 other objects, all of which left during the task, and the 5 it
  holds at step 45 all arrived during the task. A model writing every patch from the start state sees the wrong 10.
  It is the only hand-over in SC1 where every matched object arrived during the task. The selection rule of P4 (most
  objects) was too coarse: what makes a hand-over hard is how much of the start state is out of date for it.
  This is an observation after the run, not a prediction; it is turned into one in SC2 (a frozen predictor).
- **Mistral's RSOS planner proposed 3.3 invalid operations per task** (53 in 16 tasks; Gemini 0). Every one was rejected
  by the runtime before it ran and corrected within the step; all 16 tasks ended exact. On A8 the non-Claude rate was
  0.16 per task; the new scene vocabulary costs Mistral more retries. Recorded in `FAILURES_MAP.md`.

## Post-hoc check of the law (not a prediction)

A predictor trained only on A7/A8 steps (configuration state, never the robot scene; `sc2_predictor.py`, features: does
the step scan the state, how many matched keys are out of date relative to the start state, how many keys it changes,
position) ranks the 896 SC1 steps. Gemini's failure 906/45 is 4th; Mistral's 913/53 and 913/49 are 1st and 3rd;
Mistral's 906/50 is 8th. Out of sample by model on A7/A8, the predictor's AUC is 0.91–0.99 for five of six models and
0.76 for Mistral, which also fails on copy chains. SC2 freezes this predictor before its tasks exist.

## Totals

RSOS blind planning: **288 of 288 tasks exact** across Claude Haiku, Sonnet and Opus, Mistral Large 4, Gemini 3.8 Flash
and GPT-6.2 Sol, on configuration state and a robot scene; 0 wrong steps.

## Artefacts (sha256)

    256cf2c5052f0bd99958de3d86791088fab8bf86ffe0a683877c3ac2655ccc60  results/a7_results_SC1_gemini_38flash.jsonl
    a453db51d13eac2455a88925e39fc26c006198fb2b9e94559b59456b44725e87  results/a7_results_SC1_mistral_large40.jsonl
    db6b59e77c0e4ca78aa3aaa8e771468a87b3893f4395b50c36e0ad51989b7fc5  bench/statebench_v1_SC1.jsonl

Transcripts: `results/a7_transcripts_SC1_<label>.jsonl` on the run machine, added on upload.
