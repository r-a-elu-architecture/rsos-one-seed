# A8, other model families: Mistral Large 4 and Gemini 3.8 Flash (19 Nov 2026)

Pre-registration: `PREREGISTRATION_A8.md` (G1–G5) and amendments 2–8 (G6–G9, providers, pinned models, transport
fixes, analysis rule for capped calls), all committed before the runs they govern. **G9 was published in the public
repository (RSOS-Language `00e5121`, 18 Nov 2026 22:26 UTC) before any Mistral or Gemini run.**

## Strongest finding: the named-step prediction hit, on both new families

G9, published before the runs: *on L3, one-call JSON Patch (B2) fails seed 712 or 702 at step 35 on at least one of
Mistral and Gemini, while RSOS blind (X5b) ends exact on both tasks on both families* (chance level about 5%).

| Family | B2 seed 712 | B2 seed 702 | X5b 712 / 702 |
|---|---|---|---|
| **Gemini 3.8 Flash** | **failed at step 35** (REHOST, 3 attempts, 11 wrong final values); its only failure in 32 tasks | exact | exact / exact |
| **Mistral Large 4** | failed (INHERIT steps 27, 28, 43–45) | **failed at step 35** (REHOST), also steps 22 and 42 | exact / exact |

**G9: pass.** On Gemini the hit is clean: the one M\* failure of the whole family landed on the named task and step.
On Mistral the step-35 failure sits in a task with one call at the 16,000-token cap (amendment 7: reported
separately); the Gemini hit carries the verdict without it. Mistral's 702 failure steps (35, 42) are the same two
steps Haiku's B2s failed on in A8.

## Results

| Model | Cell | B2 (M\*) exact | X5b (blind) exact | B2 failed steps (kind) |
|---|---|---|---|---|
| Mistral Large 4 (`mistral-large-4-0`) | S1 | 16/16 | **16/16** | — |
| | L3 | **12/16** | **16/16** | 702: REHOST ×3; 707: FUSE ×2, INHERIT; 711: INHERIT, REHOST ×2; 712: INHERIT ×5 |
| Gemini 3.8 Flash (`gemini-3.8-flash`) | S1 | 16/16 | **16/16** | — |
| | L3 | 15/16 | **16/16** | 712: REHOST at step 35 |
| gpt-oss-120b (Groq free tier) | S1 | 16/16 | 3/3 completed (incomplete cell) | — |

Across A7 and A8, RSOS blind is now **224/224 tasks exact on Claude (Haiku, Sonnet, Opus), Mistral and Gemini**
(160 Claude + 64 new), 0 wrong steps. Every M\* failure on the new families is a state-dependent kind (REHOST,
INHERIT, FUSE).

**Tokens (L3, mean per task).** Mistral: X5b input 0.61×, output 0.60× of B2; per correct task 0.45× in USD at the
list price fixed before the run (B2 $0.156, X5b $0.070). Gemini: input 0.71×, output 0.43×; per correct task 0.61×
in tokens (free tier). Mistral's run cost about $4 of plan credit in total.

## Predictions

| # | Verdict | Evidence |
|---|---|---|
| G1 invariance | **pass on every complete cell** | X5b 16/16 in all four new cells. `a8_analyse.py` returns false only because the gpt-oss X5b cell holds 3 of 16 tasks (Groq daily quota); without that incomplete cell G1 is true (results hash `d1fa7402…`) |
| G2 error class | pass | 23 of 23 M\* failed steps state-dependent; blind 0 |
| G3 cost | pass | as before (priced models); Mistral 0.45× in USD, Gemini 0.61× in tokens |
| G4 | pass | unchanged (Haiku B2s) |
| G5 no family where M\* wins | **pass on every complete cell**; false in the script for the same incomplete gpt-oss cell (B2 16 vs X5b 3 tasks run) |
| G6 decoupling | pass (provisional) | X5b range 0 across Mistral and Gemini in both cells; B2 range on L3 = 3 (12 vs 15) |
| G7 immunity | **part 1 pass, part 2 fail** | 0 invalid operations executed (X5b: 10 proposed on Mistral, 0 on Gemini, all rejected, 0 wrong steps). Proposed per task: non-Claude 0.16 vs Claude 0.09 = 1.7×, not ≥ 3× |
| G8 same request | **not met yet** | 712 step 35 fails on Gemini and Claude; 702 step 35 on Mistral and Claude; no single step on two non-Claude families yet |
| **G9 named step** | **pass** | above |

REACH (instrument): families with blind exact = 3 (Anthropic, Mistral, Google) of target 10.

## Integrity notes

- Two failed starts on Mistral before any task completed (amendments 5, 6: `top_p`, list-shaped content).
- Nine L3 B2 tasks stopped when the owner's drive was disconnected; no outcome was recorded or seen; rerun (run note).
- The kit's `a7_openai.py` that ran is identical in code to the repository's (docstring differs only).
- gpt-oss-120b: run 1's X5b seed 302 failed (console log); the results file holds only tasks completed after the
  runner fix. Reported, not counted as a pass.

## Artefacts (sha256)

    be2014d81672693827bf1bce97c122dc142c301f7933e7084e9f7c96fbb128d9  results/a7_results_L3_gemini_38flash.jsonl
    5484c4aac7e0785616de363498de0b09ce5a9025eca4e500dd893a23d388e93c  results/a7_results_S1_gemini_38flash.jsonl
    32715e117d29739006a4f9eeb8cc9fc7448ed5e0452cdd59e47d5dd82dc26463  results/a7_results_L3_mistral_large40.jsonl
    c89982028deedda754d520f8edd09ba9e3706b7228e9726f2c186177651aa609  results/a7_results_S1_mistral_large40.jsonl
    b906aa14da5b60833eb913b0bb6ccac913ca4d80084a15d1f30f95a00d598732  results/a7_results_S1_groq_gptoss120b.jsonl

`python experiments/a8_analyse.py` (0 model calls) → `results/a8.json`, results hash `e34e7762…` with all files;
`d1fa7402…` without the incomplete gpt-oss cell.
- Public: RSOS-Language d5f2f43 (19 Nov 2026 02:36 UTC): A8 families results after the G9 prediction (00e5121, 18 Nov 22:26 UTC).

## Update, 19 Nov 2026 05:30 Kyiv: OpenAI (GPT-6.2 Sol via Codex, reasoning low) — G10 hit

G10, published before any GPT task (RSOS-Language `edcd42e`, 02:50 UTC): *on L3, B2 fails seed 712 or 702 at step 35
on GPT-6.2 Sol while X5b ends exact on both.*

| Cell | B2 (M\*) exact | X5b (blind) exact | B2 failure |
|---|---|---|---|
| L3 | 15/16 | **16/16** | **seed 712, step 35** (REHOST, 3 attempts, 11 wrong final values): its only L3 failure |
| S1 | 15/16 | **16/16** | seed 107, step 14 (REHOST): the step that failed on Haiku in A7 and A8 |

**G10: pass.** Tool use: 0 of 154 calls (clean Codex home, amendment 12). **G8 now met:** step 35 of seed 712 has
failed on Gemini and OpenAI (two non-Claude families) and on Haiku, Sonnet and Haiku B2s. The same named request has
now broken the one-call JSON Patch pattern on models from three companies; Opus and Mistral passed it (Mistral failed
712 at other steps).

Tokens per correct task, L3, with the Codex per-call overhead (16,244 input tokens, measured before the run)
subtracted: X5b 8,024 vs B2 13,183 = **0.61×**; raw 0.77×. S1: 0.93× net. Plan usage, not priced.

Totals: RSOS blind **256/256** exact across Claude Haiku, Sonnet, Opus, Mistral Large 4, Gemini 3.8 Flash and
GPT-6.2 Sol; 0 wrong steps. `a8_analyse.py` reports G1 and G5 false only from the incomplete gpt-oss cell (3 of 16
tasks), as before. G6 holds (X5b range 0 across the three new families; B2 range 3). G7 part 2 still fails
(non-Claude 0.10 vs Claude 0.09 invalid operations per blind task).

    2f506b37de93b2da44c3651de0b273b5888584cf487076e8336f26043356e067  results/a7_results_L3_codex_gpt62sol.jsonl
    cb7c22da64b6ad5bff4f5f2eeb42ed62ea6cdb05bf638fbd81f1856cf75a1c52  results/a7_results_S1_codex_gpt62sol.jsonl

`a8.json` results hash `8cb9a1fd…`.
- Archived: GitHub release v0.3.2 (commit 6cbe651) → Zenodo doi:10.5281/zenodo.24358277 (19 Nov 2026).
