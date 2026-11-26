# A3c pre-registration: the prose floor (D90, owner's 5× target)

Written before any A3c code, dragon call or run (17 Nov 2026). Brief: `BRIEF_A3C_PROSE.md`. Owner (17 Nov, 18:35):
"0 model calls" stays strict; a local model is allowed only as a separate, labelled arm.

A3b left 932 channel tokens per task for H-dragon (0.64× the tent D, BPE 0.55×) with full integrity. 87% of that
(808 tokens) is the planner's free prose, restored byte-exactly, 88% of it sent as literal text. A3c lands a **shared
predictor** on that prose: the holographic reference beam is the book; for prose it is a predictor both sides hold
identically, so only the surprise travels.

## Host, tasks, drift, harness (unchanged from A3b)

Planner → worker → checker, all `claude-haiku-5-5`, same prompts, P's flow, max 2 retries, 30-line state,
14 change requests, drifts at steps 4, 8, 12 (48 per arm). Test seeds **100–107 and 300–307**. The A3b harness
`a3b_hologram.run_task` is used unchanged; the new codecs live in new files (`a3c_*.py`) and subclass or wrap
`a3b_hdragon.HDragon`. Frozen, not edited: `a1_agents.py`, `a3_run.py`, `a3b_hologram.py`, `a3b_hdragon.py`.
Inside unchanged: every LLM prompt is built exactly as in P, and the harness asserts on every message that the
instruction, the reject reason and the state decode exactly to the text P would have carried.

## Re-use check (before any live call)

1. `git diff 9ef7933 -- experiments/a1_agents.py experiments/a3_run.py experiments/a3b_hologram.py
   experiments/a3b_hdragon.py` is empty.
2. A3's 16 recorded D runs replay through `a3_run.replay` and reproduce their A3 records (the `a3b_analyse` field
   list plus drift outcomes): 0 mismatches.
3. A3b's 16 recorded H-dragon runs replay through `a3b_hologram.run_task` with the HDragon codec (recorded LLM outputs
   fed back, every prompt asserted identical) and reproduce their A3b records (same fields, plus channel BPE): 0
   mismatches.

If all three hold, D (1,468 regex / 1,860 BPE tok/task, 16/16 exact) and H-dragon (932 / 1,023) are re-used.
Otherwise the failing arm is rerun live on all 16 seeds.

## Arms

| | Predictor for the prose | Model calls counted |
|---|---|---|
| D tent | — (re-used from A3) | — |
| H-dragon | — (A3b codec, re-used) | 0 in the codec |
| **H-pred** | deterministic, non-neural, designed by the White Dragon | **0** |
| **H-local** (labelled) | a small local language model, identical weights on both sides | reported as **local model calls** |

**The White Dragon's design comes first.** One call to `claude-opus-5-5` with the White Dragon system prompt (as A2,
A3b). The prompt gives: the host, A3b's H-dragon formats and measured costs per place, the prose statistics, the
metric with its BPE guard, the hard constraints (below), the compute budget for H-local (4 CPU cores, 15 GB RAM, no
GPU, the whole live run within about 2 hours), and the cross-domain library. It returns the design of H-pred (the
predictor, its tables, the coder, the wire format, how the bits become channel tokens) and of H-local (which open
model, how its predictions feed the same coder), with **predicted channel tokens per task for each** (regex and BPE,
total and per edge). The design is saved verbatim (`results/a3c_dragon_design.json`) and committed before any
implementation. It is implemented literally; every implementation choice where it is silent (IMPL) and every
deviation (DEV) is listed in the report. It is not revised after any test-seed result.

Prose examples shown to the dragon come only from the smoke seed 999 (A3b's smoke transcripts), not from test seeds.

## Hard constraints (both new arms)

1. Lossless: the receiver reconstructs exactly the planner's instruction and the checker's reject reason; the
   harness asserts this on every message. Integrity layer as H-dragon (snapshot repair, chk6 walls, strict edits
   decode); it may be changed only if the design says so and the B3 integrity measures still apply.
2. H-pred: deterministic code, no neural network, no model call. H-local: the only addition is the local model;
   its forward passes are counted and reported (calls, tokens processed, CPU seconds); no hosted LLM call is added.
3. Out of band, fixed before the run: the initial books, the A3b tables, and any table or priming corpus the dragon
   defines. A priming corpus may contain planner/checker prose **only from seeds disjoint from the test seeds**
   (500–531 reserved for this), generated before the run with the same planner prompt; its one-time size is
   reported (bytes, regex, BPE), not counted per task, as the books and tables are. The codec may use any history
   both sides have already seen in the task.
4. Development and debugging only on non-test seeds (999, 500–531). Any implementation change made after a
   test-seed result is listed in the report with its effect.

## Measures (as A3b)

Channel tokens per task (regex `\w+|[^\w\s]`, primary), BPE (o200k_base) and bytes, total and per edge; exact and
replica-consistent success; steps failed; drift healed with 0 model calls; offline truncation check of every
worker → checker message (5 cut fractions, full strict decode + chk6); LLM tokens billed, calls, wall-clock; for
H-local the local model's forward-pass count and CPU seconds. Bits per character of the coded prose, per arm.

## Predictions

D = 1,468 regex / 1,860 BPE tok/task (A3).

- **C1:** H-pred channel tokens ≤ 0.5 × D (≤ 734 regex **and** ≤ 930 BPE), with full integrity: 48/48 drifts healed
  at 0 model calls, 16/16 replica-consistent, 0 truncations silently accepted.
- **C2:** H-pred exact successes ≥ D's (16/16).
- **C3 (owner's target, stretch):** H-local ≤ 0.2 × D (≤ 293.6 regex **and** ≤ 372 BPE) with the same integrity;
  reported only as "with a local model".
- **C4:** the dragon's predicted channel tokens per task for H-pred within ±50% of measured (regex).

**Validity rule (as A3b):** a pass on the regex proxy counts only if the same inequality also holds in BPE tokens;
otherwise it is reported as "fail (proxy artefact)". Dense blobs that the regex counts as one token are therefore
judged by BPE.

Secondary, not pass/fail: H-local's exact successes and C4's analogue for H-local; H-pred and H-local on A3's 16
recorded P conversations (offline replay, prompts asserted identical) as a batch-independent check.

## Expected weak points (written now)

- Prose is ~4,500 characters per task (A3b H-dragon planner outputs, mean of 16). At 15 bits per channel token, C1
  needs about 1.2 bits per character overall on top of the ~124 non-prose tokens; a non-neural context model with
  only a short in-task history is typically at 2–3 bits per character on English. C1 is uncertain; a priming corpus
  is the main lever.
- C3 needs roughly 0.4–0.5 bits per character. A small CPU model is typically at 0.8–1.5; C3 is likely to fail
  unless the book context and priming make the prose highly predictable.
- Floating-point non-determinism can break arithmetic decoding for H-local; the round-trip assertion catches it,
  and a fallback, if the design has one, is counted.
- One model family, 16 tasks per arm, a new live batch for H-pred and H-local.
