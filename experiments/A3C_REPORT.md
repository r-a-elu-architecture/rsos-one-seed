# A3c report: the prose floor (D90, owner's 5× target)

Pre-registration: `PREREGISTRATION_A3C.md` (commit d291931, before any code, dragon call or run). Re-use check:
`a3c_reuse.py` → `results/a3c_reuse.json` (e208c65). Dragon call: `a3c_dragon.py`; design verbatim
`results/a3c_dragon_design.json` (99bd346, before any implementation). Codecs: `a3c_coder.py` (arithmetic coder and
word packing), `a3c_hpred.py` (H-pred), `a3c_hlocal.py` (H-local). Runner `a3c_run.py`, priming runs
`a3c_prime_runs.py`, design gate `a3c_gate.py`, analysis `a3c_analyse.py`. Results `results/a3c_prose.json`,
**results_sha256 `1d7976246d1222d10b5eabe63dac05ae6d26fc5fa8870e648aaad2f47f75ae7f`**. Runs and every message and
LLM call: `results/a3c_results_{Hp,Hl}.jsonl`, `results/a3c_transcripts_{Hp,Hl}.jsonl`.

Host as A3/A3b: planner → worker → checker, all `claude-haiku-5-5`, test seeds 100–107 and 300–307, 14 steps,
3 drifts per task. The A3b harness `a3b_hologram.run_task` was used unchanged; the frozen files were not edited.

## Strongest finding

**The owner's 5× target is reached twice. A deterministic, non-neural shared predictor reaches it with 0 model
calls; a local language model reaches it with full integrity.**

- **H-pred** (integer counts only, no neural network, 0 model calls): **261.75 channel tokens per task**, 0.178× the
  tent in regex and **0.141× in BPE** (261.75 vs 1,860). It is 0.28× A3b's H-dragon. Results: 48/48 zero-call heals,
  0 of 1,160 truncations accepted, 0 drift left in any copy. One task failed one step: the checker rejected a
  correct `DEL` three times. So H-pred has 15/16 exact and fails C1 and C2 under the pre-registered rule (below).
- **H-local** (labelled: "with a local model", Qwen/Qwen2.5-0.5B): **197.375 channel tokens per task**, 0.134× the
  tent, **0.106× in BPE**. That is about 9.4× smaller than the tent in BPE. Results: **16/16 exact, 16/16
  replica-consistent**, 48/48 zero-call heals, 0 of 1,140 truncations accepted. **C3 passes.**

A3b left 808 tokens per task of the planner's free prose, restored byte-exactly. A3c codes that prose at **0.60 bits
per character** (H-pred) and **0.41** (H-local). The mechanism is predictive coding against a reference that both
sides hold:
1. A shared priming corpus from disjoint seeds.
2. The snapshot book: keys, values and sibling order become ranks, usually rank 0.
3. The task's own history.
4. An exact arithmetic coder whose output is packed into words that each cost exactly 1 regex and 1 BPE token
   (15.5 bits per token).

Edits are coded as ranks in a list parsed from the instruction both sides already hold (rank 0 ≈ 0.3 bits). The
6-digit check value then dominates the edits message, which is 2 words.

## Results (means per task, 16 tasks)

| | D · tent (A3) | H-dragon (A3b) | **H-pred** | **H-local** (local model) |
|---|---|---|---|---|
| Channel tokens, regex (95% CI) | 1,468 | 932 | **261.75** (239.1–290.6) | **197.375** (188.1–208.6) |
| Channel tokens, BPE o200k | 1,860 | 1,023 | **261.75** | **197.375** |
| Channel bytes | 4,930 | 3,156 | 1,729 | 1,272 |
| × D (regex / BPE) | 1 / 1 | 0.64 / 0.55 | **0.178 / 0.141** | **0.134 / 0.106** |
| Prose bits per character (instructions) | — | — | 0.598 | 0.415 |
| Reject reasons, bits per character | — | — | 1.79 (9 reasons) | 1.19 (4 reasons) |
| Exact success | 16/16 | 16/16 | 15/16 | **16/16** |
| Replica-consistent success | 0/16 | 16/16 | 15/16 | **16/16** |
| Wrong final lines | 0 | 0 | 1 | 0 |
| Steps failed after 2 retries | 0 | 0 | 1 | 0 |
| Drift healed with 0 model calls | 0/48 | 48/48 | **48/48** | **48/48** |
| Drift in any copy at the end | 40 | 0 | 0 | 0 |
| Truncations silently accepted | 13/1,150 | 0/1,140 | **0/1,160** | **0/1,140** |
| Hosted LLM calls / LLM tokens billed | 42.8 / 83,563 | 42.5 / 82,986 | 43.0 / 83,563 | 42.5 / 83,004 |
| Local model forward passes (whole run) | — | — | 0 | 37,887 |
| Wall-clock per task (s) | 191 | 176 | 218 | 3,182 |

**Per edge (tokens per task; regex = BPE in both new arms):**

| Edge | D | H-dragon | H-pred | H-local |
|---|---|---|---|---|
| Instruction | 1,093 | 808 | **168.75** | **119.0** |
| Edits | 134 | 44 | 29.8 | 29.8 |
| Door (approve `+` = 14/task, plus reasons) | 111 | 32 | 34.6 | 19.4 |
| Forward | 130 | 49 | 28.6 | 29.1 |
| Heal | — | 0 | 0 | 0 |

The priming corpus and model weights are one-time and out of band, like the books and tables:
- Priming corpus: 32 H-dragon runs on seeds 500–531 (1,366 Haiku calls, $0.59): 448 instructions and 12 reject
  reasons, 138,479 bytes (37,924 regex / 38,389 BPE tokens).
- Frozen H-pred model: 341,451 bytes, sha256 `0d40a312…`.
- Word alphabets: A0 = 10,483 words, A1 = 47,424 words.
- H-local's Qwen2.5-0.5B weights: about 988 MB, snapshot `060db649…`.

## Predictions

| | Prediction | Result | Verdict |
|---|---|---|---|
| C1 | H-pred ≤ 0.5 × D (≤ 734 regex and ≤ 930 BPE), with 48/48 zero-call heals, 16/16 replica-consistent, 0 truncations accepted | Size 261.75 / BPE 261.75 (0.141× D) **passes**; 48/48 heals and 0/1,160 truncations **pass**; replica-consistent **15/16** | **Fail** |
| C2 | H-pred exact ≥ D's 16/16 | 15/16 | **Fail** |
| C3 | H-local ≤ 0.2 × D (≤ 293.6 regex and ≤ 372 BPE) with the same integrity, "with a local model" | 197.375 / BPE 197.375 (0.106× D); 48/48, 16/16, 0/1,140 | **Pass** |
| C4 | Dragon's H-pred prediction within ±50% of measured | predicted 276, measured 261.75 (+5.4%) | **Pass** |

Scoring rule for C1, as for H-copy's B3 in A3b: replica_success must be 16/16, with no exception for LLM errors.
Validity rule: every regex pass also holds in BPE, because the new arms' channels count the same in both by
construction. Secondary checks:
- The dragon's H-local prediction was 205, measured 197.375 (−3.7%).
- H-local exact successes: 16/16.

## What failed and why

- **C1 and C2: one checker error on seed 300.** At the step "Remove the line cache.region entirely", the worker
  output `DEL cache.region`, which is correct. The checker rejected it three times. Each time it claimed that the
  baseline contains no `cache.region` key. The planner's instruction listed every remaining key, which may have led
  it there. The step was left undone: `cache.region` stayed in the state, and all three copies agree but are wrong.
  - It was not a codec failure. The checker's prompt is built exactly as in P (frozen harness). The decoded
    instruction, the edits and the state were asserted byte-exact on every message.
  - It is the same failure class as H-copy's B3 and B4 in A3b, and it counts.
  - The offline replay of A3's 16 recorded P conversations through H-pred gave 16/16 exact and 16/16
    replica-consistent, at 271 tokens per task.
- **Reject reasons are the least-predicted prose.** H-pred codes them at 1.79 bpc, from only 12 reasons in the
  priming corpus (the dragon's risk 9). They still cost only about 20 tokens per task.
- **The fixed floor is now the check values.** Edits plus forward cost about 58 tokens per task, two 2-word
  messages per step, because chk6 (≈ 20 bits) is kept on both edges as in A3b. The dragon's chk10 option would
  save about 14 tokens per task. Not taken: it weakens the forward check.

## Mechanism details (measured)

- **H-local mode choice:**
  - 169 of 228 prose messages went in LLM mode.
  - 59 went in H-pred mode, chosen because it was shorter.
  - 3 went in H-pred mode because their context was over 2,600 tokens.
  - 0 NAKs; the decode never desynchronised.
- **Local model cost:**
  - Forward passes: 20,486 encoder side, 17,400 decoder side, 1 preamble = **37,887**.
  - Payload tokens coded: 20,258.
  - The whole process used 16,372 CPU seconds and 6,422 s of wall-clock (4 cores, one model call at a time), so a
    task took 3,182 s against H-pred's 218 s.
  - These are local model calls, reported separately from the 0 hosted calls they add.
- **Design gate** (the dragon's, run on dev seeds only before any test seed):
  - 32-way leave-one-out over the priming runs gave H-pred 233.1 tokens per task at 0.561 held-out bpc, under the
    design's 0.72 threshold.
  - Live on test seeds: 0.598 bpc and 261.75 tokens per task.
- **Edits fallbacks:** 0 in both arms. Instruction fallbacks: 0.

## Re-use check and integrity of this run

- `git diff 9ef7933` of `a1_agents.py`, `a3_run.py`, `a3b_hologram.py` and `a3b_hdragon.py` is empty.
- A3's 16 D runs and A3b's 16 H-dragon runs replay through the current harness and reproduce their records with
  **0 mismatches**, including H-dragon's BPE: 932.4375 / 1,023.3125. D and H-dragon are re-used.
- Inside unchanged: in both arms, `run_task` asserts on every message that the instruction, the reject reason and
  the state decode exactly to what P carries. No assertion failed in 32 live tasks, 32 priming replays, 16 + 16
  offline replays, or the 32 gate folds.
- Truncation was checked **in-line** in the live run against the codec's live adaptive state: every worker →
  checker message, 5 cut fractions, full strict decode plus chk6. A3b did this offline. The adaptive codec needs
  the state at that moment, so the check runs where that state is. It was decoded against the worker's book, which
  equals the checker's book at every step, since drift touches only the worker.
- **Run handling.** The first H-local launch was killed for lack of memory (8 task threads loaded the model at
  once, 13 GB). This happened inside `new_task`, before any LLM call, and nothing was recorded. I added a load
  lock (commit c8c4a9a) and restarted. This was the only change after the frozen model was committed, and
  it came before any H-local test-seed result. H-pred's live run was not affected.

## IMPL / DEV list (the design was implemented literally otherwise)

- **IMPL, lexer:**
  - WORD is ASCII only (`[A-Za-z_][A-Za-z0-9_]*`), WS is `[ \n\t\r]+`, NUM is 1–7 digits.
  - Any other single character is a PUN unit.
  - The initial skeleton vocabulary is the 5 tags plus END.
  - Every novel literal (word, whitespace or punctuation) joins the vocabulary.
  - Whitespace spelling is uniform.
- **IMPL, PPM:**
  - The escape frequency is the number of non-excluded symbols in the context.
  - An order whose symbols are all excluded is skipped.
  - An order is skipped when the history is shorter than it.
  - Rank tables are halved at 2^13, as the PPM counts are.
- **IMPL, candidates:**
  - lastS is the more recent of the last SVC and lastK's service.
  - With no SVC yet, the first S candidate is the first service of the book.
  - R mode puts the instruction's and the edits' keys and values right after the in-message items.
  - Arithmetic candidates skip negative results and division by 0.
- **IMPL, edits:**
  - Canonical op order: sets in book order, then deletes in book order, then adds in new order.
  - VALUE carries a model/raw flag (adaptive, starting at 15:1); raw values are UTF-8 bytes.
  - tier values are taken from WORD units.
  - Edits-model updates are applied on approval.
  - chk6 is A3b's chk6.
- **IMPL, H-local:**
  - A tie between the two modes goes to LLM mode.
  - The H-pred model is updated on every message in both modes.
  - Trigram words are `\w+`, lowercased.
- **DEV:**
  - The design's fresh-process proofread decode was not run (the design's risk 5 allows dropping it). chk8, the
    canonical check and the `?` NAK fallback remained, and were used 0 times.
  - The A3b H-dragon edits format behind `~` was available for edits the op grammar cannot carry, and was used
    0 times.

## Limits

- One model family, 16 tasks per arm; the H-pred and H-local batches were new and separate.
- H-local is a local-model claim. It costs 37,887 forward passes and about 15× H-pred's wall-clock on 4 CPU cores.
  Its weights (about 988 MB) are a one-time, out-of-band table, like the priming corpus.
- The priming corpus comes from the same agents, prompts and task generator, on disjoint seeds. The gain depends on
  the shared prose style, which is the point of a shared reference, but a different planner model would need its
  own corpus.
- The zero-token heal still relies on the untouched snapshot (as in A3b). The check values are 20 bits (chk6) and,
  for H-local prose, 8 bits (chk8).
- Latent drift in a copy that is read for computation is still untested; that is A4.

## Next discovery action

The channel is now about 60% prose and about 40% integrity. The strongest successor tests:
1. **Prime the door** with reject reasons from more disjoint runs. Reasons are at 1.2–1.8 bpc against 0.4–0.6 for
   instructions.
2. **One check value per step instead of two**, by binding the edits and forward checks to one hash of the agreed
   state. That would save about 14 tokens per task without weakening the check.
3. **Cross-model A3c**: the same codecs, with a different planner model on the same seeds. This tests whether the
   predictor generalises or only memorises Haiku's style.
