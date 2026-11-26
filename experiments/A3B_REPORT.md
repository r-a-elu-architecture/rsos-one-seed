# A3b report: the hologram palace (D90)

Pre-registration: `PREREGISTRATION_A3B.md` (commit 2a2d65b, before any code, dragon call or run). Dragon call:
`a3b_dragon.py`; design verbatim `results/a3b_dragon_design.json` (commit be4c362, before implementation and before
any H run on a test seed). Harness `a3b_hologram.py` (imports `a1_agents.py` unchanged), H-dragon codec
`a3b_hdragon.py`, analysis `a3b_analyse.py`. Results `results/a3b_hologram.json`, **results_sha256
`0ae0d0315ac392184128252c5d8b57eabfc9c977f10eb6e02b6f7eda20507120`**. Runs: `results/a3b_results.jsonl` (H-copy),
`results/a3b_results_hd.jsonl` (H-dragon), merged in `results/a3b_runs.json`. Every message and LLM call:
`results/a3b_transcripts.jsonl` and `results/a3b_transcripts_hd.jsonl`.

Host as A3: planner → worker → checker, all `claude-haiku-5-5`, seeds 100–107 and 300–307, 14 steps, 3 drifts per
task. 32 new task runs (16 per H arm), 1,374 LLM calls, $0.60, plus the dragon's call ($0.70, `claude-opus-5-5`,
368 s). P, D and E are taken from A3, after the re-use check below passed.

## Strongest finding

**The White Dragon's hologram is the first protocol in A1–A3b that is smaller than the tent and also keeps every copy
true.**

- H-dragon used **932 channel tokens per task**: 0.64× the tent (D, 1,468) and 0.35× the palace (P, 2,699). In BPE
  tokens it was **1,023**, 0.55× D's 1,860, so the gain is not an artefact of the regex token proxy.
- It reached **16/16 exact and 16/16 replica-consistent**, against D's 16/16 exact and 0/16 replica-consistent.
- It healed **48/48 drifts with 0 model calls and 0 channel tokens**.
- It accepted **0 of 1,140 truncations** (228 messages × 5 cut fractions).
- It failed 0 steps.

The owner's 5× target was not reached: the hologram is 1.57× smaller than the tent, not 5×. The reason is measured
exactly. Every place the dragon landed fell close to the floor:

| Place | P | H-dragon | Reduction |
|---|---|---|---|
| Door | 854 | 32 | 27× |
| Edits | 196 | 44 | 4.5× |
| Forward | 187 | 49 | 3.8× |
| Heal | 114 | 0 | — |

Together these non-instruction places cost **124 tokens per task**, 8.4% of the tent and already below the 294 target
on their own. **87% of what remains (808 tokens) is the planner's free prose.** It must be restored byte-exactly (the
owner's "everything is there and the same"), and 88% of it went out as literal text, because Haiku's phrasing rarely
falls into the dragon's templates. The integrity layer was not the barrier to 5×; the lossless prose was.

## Results (means per task, 16 tasks; P, D, E from A3)

| | P · palace | D · tent | **H-copy** | **H-dragon** |
|---|---|---|---|---|
| Channel tokens, regex (95% CI) | 2,699 | 1,468 | 1,290 (1,213–1,373) | **932** (873–993) |
| Channel tokens, BPE o200k | 3,131 | 1,860 | 1,695 | **1,023** |
| Channel bytes | 10,062 | 4,930 | 4,142 | **3,156** |
| × D (regex / BPE) | 1.84 / 1.68 | 1 / 1 | 0.88 / 0.91 | **0.64 / 0.55** |
| Exact success | 16/16 | 16/16 | 12/16 | **16/16** |
| Replica-consistent success | 16/16 | 0/16 | 12/16 | **16/16** |
| Wrong final lines | 0 | 0 | 8 | **0** |
| Steps failed after 2 retries | 2 | 0 | 3 | **0** |
| Drift healed with 0 model calls | 48/48 | 0/48 | 47/48 | **48/48** |
| Drift in any copy at the end | 0 | 40 | 1 | **0** |
| Heal channel tokens per healed drift | 37.9 | — | 2.0 | **0** |
| Truncations silently accepted | (shape check only) | 13/1,150 | 0/1,175 | **0/1,140** |
| LLM tokens billed | 84,790 | 83,563 | 84,468 | 82,986 |
| LLM calls | 43.1 | 42.8 | 43.4 | 42.5 |
| Wall-clock (s) | 192 | 191 | 176 | 176 |

**Per edge (regex / BPE tokens per task):**

| Edge | P | D | H-copy | H-dragon |
|---|---|---|---|---|
| Instruction | 1,349 / 1,443 | 1,093 / 1,350 | 1,048 / 1,326 | **808 / 817** |
| Edits | 196 / 352 | 134 / 187 | 76 / 139 | 44 / 85 |
| Door | 854 / 803 | 111 / 141 | 87 / 91 | 32 / 32 |
| Forward (incl. H-dragon's `?` on a miss) | 187 / 336 | 130 / 181 | 71 / 131 | 49 / 89 |
| Heal | 114 / 198 | — | 8 / 9 | 0 |

D's one-time concept table (202 tokens) is used by H-copy too. H-dragon's tables T0–T7 are 450 tokens by the dragon's
own estimate. All tables are excluded from the per-task channel, as P's initial books are.

## Predictions

| | Prediction | H-copy | H-dragon |
|---|---|---|---|
| B1 | H ≤ D (1,468), also in BPE | 1,290 (0.88×), BPE 0.91× · **Pass** | 932 (0.64×), BPE 0.55× · **Pass** |
| B2 | H ≤ 0.2 × D (293.6) | 1,290 · **Fail** | 932 · **Fail** (3.2× the limit) |
| B3 | 48/48 zero-call heals, 16/16 replica-consistent, 0 silent truncations | 47/48, 12/16, 0 · **Fail** | 48/48, 16/16, 0 · **Pass** |
| B4 | H exact ≥ D (16) | 12 · **Fail** | 16 · **Pass** |
| B5 | H-dragon ≤ H-copy, with B3 | 932 ≤ 1,290 (BPE 1,023 ≤ 1,695), B3 holds · **Pass** | |
| B6 | Dragon's prediction within ±50% | | predicted 321, measured 932 (−66%) · **Fail** |
| B7 | Heal tokens per healed drift ≤ 0.25 × E (≤ 24.0) | 2.0 · **Pass** | 0 · **Pass** |

No pass in this table depends on the regex proxy: every pass on B1 and B5 also holds in BPE tokens.

## What failed and why

- **B2 (5×) failed for both arms.** The cause is measured. H-dragon's non-instruction places total 124 tokens per
  task. Its instruction edge is 808, and 11,405 of its 12,934 instruction tokens (88%) are literal prose inside
  « » literals. In 53 of 224 instructions no template matched at all. Dictionary entries were re-used in only 4
  instructions: the planner almost never repeats a sentence shape within a task. Reaching 294 would need about 170
  instruction tokens per task, about 12 per step, for prose that must be restored byte-exactly.
- **B6 failed.** The dragon fitted its templates to the two example steps it was shown (89 → 8 and 191 → 3 tokens,
  both reproduced exactly by the implementation). It flagged that assumption itself: "template coverage … decides
  whether the result lands at about 260 or about 400." Coverage was low, so the result landed at 932. The dragon was
  right about its weak point but wrong about the size. The predictive forward missed on 131 of 224 approvals,
  because the planner's prose rarely gives its codec the state, so F_final was not the approved state. Each miss
  cost `?` plus the edits message.
- **H-copy's B3 and B4 failures are LLM errors, not codec failures.** The codec cannot cause them: in both H arms
  every LLM prompt is built exactly as in P, which the offline replays below confirm.
  - Seed 102: at step 1 ("Remove the line cache.region") the worker deleted the whole six-line `cache` block, and
    the checker approved it. All three copies agreed and all were wrong. At step 4 the scheduled drift hit
    `cache.log_level`, which the book had already lost. Its line count differed, so the reference restore declined,
    and the chunk heal synced the worker to the (wrong) planner book. This is the one non-zero-call heal.
  - Seeds 104, 105 and 301: one step each was rejected three times and left undone.
  - P on the same prompts in A3 had 2 failed steps and 16/16 exact; H-dragon had 0 and 16/16 in this batch. The
    spread is run-to-run LLM variance at n = 16. The hologram guarantees copies agree; it cannot make an approved
    edit right.

## Re-use check and integrity of this run

- `git diff 8408a00 -- experiments/a1_agents.py` is empty. All 48 recorded A3 P, D and E runs replay through the
  current harness and reproduce their A3 records (success, line accuracy, replica success, final errors, failed
  steps, calls, channel tokens and bytes, billed and output tokens, drift outcomes), with 0 mismatches. A3's P, D
  and E are therefore re-used.
- **"Inside unchanged" verified offline (not pre-registered as a measure).** A3's 16 recorded P conversations were
  replayed through both H codecs with every prompt asserted identical, and all passed. On those identical LLM
  outputs:
  - H-copy: 1,260 tokens per task, BPE 1,664.
  - H-dragon: 937, BPE 1,032.
  - Both: 16/16 exact and 48/48 zero-call heals.

  H-dragon's live result (932) matches its replay (937). The live gap to D does not come from batch luck.
- **Dragon call.** The first attempt ran through `A.llm`, whose 180 s per-call timeout plus retries killed every
  attempt before any output; my 600 s wrapper then stopped the script. No design was returned, so nothing was
  discarded. The single successful call used one attempt with a 25-minute timeout and the same prompt (commits
  dd8ecac → be4c362).
- **Implementation changes after the first H-dragon replay, before any live H-dragon run** (design unchanged):
  1. A backticked key followed by "." was not turned into a macro. This was a bug.
  2. IMPL cost guard: a list match that needs hidden H/Z items is taken only if it is cheaper than the literal. One
     replayed instruction had used 26 Z items. Replay before the fix: 975 tokens per task; after: 937.
- **H-dragon IMPL/DEV list** (in `a3b_hdragon.py`):
  - Which spans become § macros (keys, services, and a value right after its key).
  - A whole-text literal fallback if the encoder's round trip fails: 0 uses.
  - DEV: H-copy-format edits behind `~` for edits the grammar cannot carry: 0 uses.
  - The design's fallback chunk heal is implemented, and used live only on a failed strict decode: 0 uses.
- **Run handling.** The H-dragon main run was started once, then stopped within seconds and restarted with its own
  transcript file, so that two processes would not interleave lines in one file. No result had been written. Any
  LLM calls still in flight at the stop are not in the recorded cost.
- **H-copy's harness code.** The H-copy main run used the harness as it was before the interface refactor. The
  refactor was verified byte-identical on all 16 H-copy replays: every message, token and byte the same.

## Limits

- One model family, 16 tasks per arm, CLI-default temperature. P, D and E come from the A3 batch, H from a new batch.
- The zero-token heal relies on a second copy (the snapshot) that the drift model does not touch. E had the same rule
  in A3. With both copies corrupted, H-dragon's fallback chunk heal costs **18.5 tokens per drift** (offline,
  measured on the 48 drift states; within B7's 24) and H-copy's A1 chunk heal 37.6, and detection then comes only at
  the checker, after the worker's call.
- The check value is 6 digits (about 20 bits). Its collision risk, about 2×10⁻⁴ over the 16 tasks, is the dragon's
  estimate, not a measurement.
- The task never reads another agent's copy for computation. That is still what hides D's latent drift. A4 remains
  the test of it.

## Next discovery action

**A3c: a shared predictor as the reference beam for the prose.** The remaining 87% is free text that must be
restored exactly. Holography's reference beam here is the shared book; for prose, the equivalent is a predictor both
sides share. Deterministic arithmetic coding against a small local language model (identical weights on both sides,
not an agent call) is lossless and typically reaches 1–2 bits per character on English. Projection, not a result:
808 instruction tokens → about 150–250, total about 280–370 tokens per task, i.e. the 5× target at the edge of reach
with integrity unchanged.

**Owner decision needed:** does a local deterministic model inside the codec count under constraint 2 ("no extra LLM
calls")? The alternative needs no new model but changes the inside: the planner emits the structured edits directly
(about 15 tokens per step). That would break "everything the same" for the instruction text, so it is the owner's
call, not mine.
