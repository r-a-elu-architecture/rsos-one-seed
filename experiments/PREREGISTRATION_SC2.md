# Pre-registration SC2: the first predicted gap of the operation table

Fixed 19 Nov 2026, 08:40 Vilnius (06:40 UTC), **before the operation is built**, before any SC2 task exists and before
any SC1 result was seen. Decision D102. Table and law: `experiments/OPERATION_TABLE.md`.

## 1. What is predicted

The operation table orders Core operations by what they read and write. One cell is empty: an operation that **scans
the whole state and computes a new value for every match** (gap D). No such operation exists in RSOS Core, in the A7/A8
harness or in any task run so far. The measured law (one-call JSON Patch fails more often the more of the state it must
read itself: 0.00% when it reads nothing, 0.14–0.17% for one or two keys, 2.31% for a whole-state scan; RSOS blind 0
failures on every row) predicts its properties before it is built.

## 2. The operation (form fixed now)

Core: `derive_where(field, cond_field, equals, add, max)`. For every object `o` with `o.cond_field = equals`:
`o.field := min(int(o.field) + add, max)`. Atomic with the step; no match is not an error; `E_NOT_INTEGER` if a matched
value is not an integer; `E_NOT_KEY`/`E_PARSE` as in Core. Deterministic. RSOS keyword: named by the language's author
from the symbols before the build, and recorded here as an amendment before any run.

Request template (robot scene): "Move every object owned by {robot} {n} cell(s) {right|up} ({x|y} plus {n}, capped at 9)."

## 3. Tasks

The SC1 scene and generator (`experiments/sc1_tasks.py`: 50 objects, 300 keys, 56 requests, depth 4, three drift
events), new seeds **1000–1015**, with **8 of the 56 requests per task** of the new kind, placed by the seed; the
`reassign_where` hand-overs of the SC1 mix stay in, so both scan kinds are measured in the same runs. 128 new-kind
requests per model. Exported to `bench/statebench_v1_SC2.jsonl` with its sha256 before any run.

## 4. Arms, models, settings

As SC1 (A8 settings): B2 (one-call JSON Patch with literal values from the full state, one audit) and X5b (RSOS blind),
Mistral Large 4 and Gemini 3.8 Flash, temperature 0, top_p 1, 2 workers. The X5b planner grammar gains one line
describing the new operation; that is the only prompt change, applied before any run. A zero-call replay check must
pass first (oracle plans exact on every arm, every drift repaired at 0 calls, no value reaching the blind planner).

## 5. Predictions

| ID | Prediction | Pass when |
|---|---|---|
| **Q1** | RSOS blind stays exact on the new operation | X5b exact on 16/16 on each complete model, 0 failed `derive_where` steps |
| **Q2** | **The gap's JSON Patch failure rate, predicted from the law** | B2 fails ≥ 5% of `derive_where` requests, pooled over the complete models (≥ 7 of 128 per model on average) |
| **Q3** | The law's ordering holds inside one run | B2 failure rate per request: `derive_where` > `reassign_where` > one-key operations, pooled |
| **Q4** | The channel saving is largest on the new row | RSOS program + digest ≤ 0.1× the bytes of JSON Patch + digest on `derive_where` steps (0 model calls, measured at export) |
| **Q5** | A new operation is learnt from one grammar line | X5b proposes ≤ 1 invalid operation per task on average (all rejected before they run) |

Basis for Q2: `reassign_where` 2.31% across all A7/A8 models; `derive_where` adds a value read and an arithmetic step
per match, each of which alone added failures on the one-key rows. The prediction is that the effects compound, to at
least twice the scan rate.

## 6. What would count against the law

Q2 failing (JSON Patch handles the new row at the rate of the one-key rows) means the law's first factor (scanning) does
not compound with the second (computing); the table then orders but does not predict. Q1 failing means blind planning
does not extend to a new operation learnt from its description, and is reported first.

## 7. Order

This pre-registration published now, before the SC1 results → RSOS name chosen → operation built in Core (registry status
`specified` → `implemented` → `tested`) and in the harness → SC2 tasks exported with sha256 → replay check → runs →
`experiments/sc2_analyse.py` (written before the runs) → report, confirming or not.

## Amendment 1 (19 Nov 2026, 08:39 Vilnius; before the build, before any run)

RSOS name chosen by the language's author: **FLOW** (owner, 08:39, after weighing FLOW, SHIFT, BEAM, MOVE and LIGHT;
LIGHT, proposed first at 08:34, stays the White Dragon's light and the origin of `reconcile`). FLOW is the language's
existing statement `FLOW <source> DIRECTION … TO …` (register U3, U22: a flow with a direction), used in the state
syntax with an OVER clause:

    FLOW x OVER owner rover +1 CAP 9      ≡  derive_where(field=x, cond_field=owner, equals=rover, add=1, max=9)

"Everything of rover flows one cell on, at most to the edge." Nothing else changes.

## Amendment 2 (19 Nov 2026, 09:35 Vilnius / 07:35 UTC; FLOW built and tested, no SC2 task drawn, no SC2 model call)

**The law as frozen code.** `experiments/sc2_predictor.py` computes, for every step of any task, the probability that
one-call JSON Patch fails there, from the task alone: does the step scan the state; how many of the keys it matches
are out of date relative to the start state (arrived or left during the task, or changed since); how many keys it
changes; its position. Logistic weights fitted on every JSON Patch step of A7, A8 and SC1 (14,560 steps, 36 failed),
`experiments/sc2_predictor_weights.json`. Out of sample by model (fit on the others): AUC 0.91–0.99 for five models,
0.82 for Mistral Large 4. Frozen now:

    predictor (code + weights)   0c976ed0dba98c20f43a92eeeeba25ebf001519175811826843af204999068f3
    sc2_predictor.py             f211740c0a2c398add287fef7ad8241e948e86b8b40f93fc9f60c886c0b9e4de
    sc2_predictor_weights.json   7091a630c17dd341c7b55d367d8f0d5ac2fc3bfa48e00b6649d43fded7ae49f0
    sc2_tasks.py (generator)     9b851d123cd0796ea97dd8f275bc2248d46fe82c2a58b59b589f659376d1ca40

`sc2_analyse.py` refuses to score if the predictor's hash differs.

**Nobody chooses the tasks.** The 16 task seeds come from the public drand randomness beacon (League of Entropy mainnet,
default chain, 30-second rounds, genesis 1595431050), **round 6654866, emitted at 08:30:00 UTC on 19 Nov 2026**, after
this amendment is public: seed_i = first 8 bytes of sha256("<randomness>:SC2:<i>"), i = 0..15 (`sc2_tasks.seeds_from`).
Anyone can fetch the round (`https://api.drand.sh/public/6654866`) and check its signature. The round's randomness is
written to `experiments/sc2_beacon.json`; the tasks are exported to `bench/statebench_v1_SC2.jsonl` with their sha256;
the predictor's top-10 steps, its expected count and the channel ratio (Q4) are computed and published before any
model call.

**Two laws, one run.** The sentence-law (Q2, fixed 06:33 UTC) says scanning and computing compound: JSON Patch fails
≥ 5% of FLOW requests. The frozen predictor has never seen an operation that computes per match and treats FLOW like a
hand-over: on dry-run tasks it expects 3.9% (about 5 of 128 per model). The run decides between them; neither is
changed.

**Added predictions:**

| ID | Prediction | Pass when |
|---|---|---|
| **Q6** | The frozen predictor's count | pooled JSON Patch failed steps (all kinds, complete models) inside the 95% Poisson interval of (models × the predictor's expected failures per model on the drawn tasks) |
| **Q7** | **Its places** | the predictor's AUC on the drawn tasks ≥ 0.8, pooled, and at least one JSON Patch failure falls on its top-10 steps (published at the draw, before the run) |
| **Q8** | The form of the error | ≥ 50% of the keys JSON Patch gets wrong on failed scan steps (FLOW and hand-overs) are out-of-date keys: objects that arrived, left, or changed during the task |
| **Q9** | Families never tested on StateBench | RSOS blind exact 16/16 on DeepSeek V4.1 Flash (`deepseek-v4-1-flash-1017`) and GLM 5.3 (`zai-glm-5-3`), through the owner's Mistral API, if run; a cell that does not complete is reported as such |

Q1–Q5 unchanged. Scoring: `experiments/sc2_analyse.py` (written now, before the draw); Q4 at export.

## Amendment 3 (19 Nov 2026, 09:45 Vilnius / 07:45 UTC; before the beacon round, before any SC2 model call)

**A control condition, SC2-C** (owner, 09:33: run the normal and the new test so the difference can be shown).
`experiments/sc2c_tasks.py` (sha256 `98f88c39d6029dcf759d7701ce3e9475463c5611ceb39fa4af773e57f37abe59`) takes the SC2 tasks from the same beacon seeds and
changes only the wording of the 8 FLOW requests per task: the request names the objects ("Move box, lamp and bottle 1
cell up (y plus 1 each, capped at 9)") instead of describing them ("Move every object owned by arm 1 cell up"). The
objects named are exactly those the FLOW request moves at that step. States, truths, drift and every other request are
identical (checked: equal truths and final states; zero-call replay check passes on every arm). A planner needs to find
nothing in SC2-C; it still computes every value.

| ID | Prediction | Pass when |
|---|---|---|
| **Q10** | **Finding the objects in a changed state is the cause** | pooled over models complete in both cells: JSON Patch fails ≥ 2 FLOW-worded steps and its failure rate on them is ≥ 2× its rate on the same steps worded with named objects |
| **Q11** | RSOS blind is exact either way | X5b exact 16/16 on SC2-C on every model run |

Models: SC2-C runs on Mistral Large 4 and Gemini 3.8 Flash (SC2 runs on these and, if possible, on DeepSeek V4.1 Flash,
GLM 5.3 and Claude Haiku 5.5 through the owner's Claude plan, label `haiku55`). Scoring: `experiments/sc2c_analyse.py`,
written now. Nothing else changes.

## Draw record (19 Nov 2026, 08:38 UTC; after beacon round 6654866, before any SC2 or SC2-C model call)

Beacon fetched by the owner at 10:38 Vilnius: round 6654866, randomness
`c59f38b3bd6ae5439f40425035a278b24133af8a63aa7ad262b466bbcf2097af`, verified as sha256 of the round's signature
(`experiments/sc2_beacon.json`). Tasks exported: `bench/statebench_v1_SC2.jsonl` sha256
`dc1b56b501dbed9c18b6198fb4863b8f8395e54fc9b5468bde2e7e65eaaa5918`; `bench/statebench_v1_SC2C.jsonl` sha256
`2d8e0834d4f6de1090f362cc4255d13c36174687b655910431778d16fffa11c2`. Zero-call replay checks pass on both
(`results/a7_replay_check_SC2_default.json`, `..._SC2C_default.json`).

The frozen predictor (sha256 `0c976ed0…`, checked) on the drawn tasks (`results/sc2_predictions.json`):

- expected JSON Patch failed steps per model: **7.63**, of which **6.43 on the 128 FLOW steps (5.0%)**; on the drawn
  tasks the code and the sentence-law (Q2, ≥ 5%) now nearly agree. Q6 intervals (95%, pooled): 2 models 7–23, 3 models
  13–33, 4 models 19–42, 5 models 26–51.
- **Top 10 places (Q7)**, all FLOW steps (seed, 1-based step, p):

| Rank | Seed | Step | p | Request |
|---|---|---|---|---|
| 1 | 1959694601287679767 | 55 | 0.399 | Move every object owned by rover 1 cell up |
| 2 | 10840159190577930439 | 37 | 0.362 | Move every object owned by arm 2 cells right |
| 3 | 7990942759714046115 | 46 | 0.270 | Move every object owned by rover 1 cell up |
| 4 | 13043114479224168765 | 55 | 0.269 | Move every object owned by scout 1 cell right |
| 5 | 13529441524361763318 | 45 | 0.253 | Move every object owned by arm 1 cell up |
| 6 | 1959694601287679767 | 34 | 0.241 | Move every object owned by rover 1 cell up |
| 7 | 11370350256784163472 | 43 | 0.215 | Move every object owned by crane 1 cell up |
| 8 | 7990942759714046115 | 41 | 0.205 | Move every object owned by drone 1 cell right |
| 9 | 13043114479224168765 | 54 | 0.200 | Move every object owned by arm 1 cell up |
| 10 | 2112855733707263979 | 50 | 0.194 | Move every object owned by rover 1 cell right |

- **Q4 (channel, measured at export): missed.** RSOS program + digest on the 128 FLOW steps: 5,726 bytes; JSON Patch +
  digest: 54,826 bytes; ratio **0.104×**, not ≤ 0.1×. Published as a miss before any run.
