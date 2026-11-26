# Pre-registration: agents phase 3 (confirmatory), 22 Nov 2026 ~13:45 Kyiv

Written after phase 1d (RESULTS_PHASE1D.md) and before any phase 3 call. Sealed in SEAL_AGENTS_PHASE3.txt.
Nothing here may change after the seal. Analysis: `analyze_phase3.py` (sealed with this file).

## Fixed
- **Structure:** rsos_01100 (roles detect + adapt; barrier, memory, reg off), chosen in phase 1d on gpt-oss-20b.
- **Baselines:** react, reflexion, selfcons, planexec (plain dropped: no tools, 0.01 in phase 1d).
- **Models (OpenRouter):** openai/gpt-oss-20b (selection model), openai/gpt-oss-120b, qwen/qwen3.8-27b, meta-llama/llama-4-scout.
- **Tasks (all new):** staff seeds 5000–5149 (held-out family: never used for selection) and orders seeds 3000–3149
  (selection family, new tasks). 300 tasks × 4 models = 1,200 paired units per arm. GSM8K dropped: phase 1 showed
  arithmetic-only families hit the ceiling (plain 0.95).
- **Harness:** design v3 (tools declared natively, reply 1,500 tokens, task budget 16,000 tokens, 12 calls), the code
  hashed in the seal.

## Step 0: plumbing check per model (before any phase 3 task)
`python run.py --models <the 3 new models> --family orders --seeds 4-6 --arms react,rsos_01100 --design v3 --out smoke3.jsonl`
then `python emptycheck.py smoke3.jsonl` per model (the check is pooled; if it fails, run per model). A model with more
than 10 % empty replies is **excluded** and reported; phase 3 runs on the rest. gpt-oss-20b already passed (smoke1d).

## Runs
`python run.py --models openrouter:openai/gpt-oss-20b,openrouter:openai/gpt-oss-120b,openrouter:qwen/qwen3.8-27b,openrouter:meta-llama/llama-4-scout --family staff --seeds 5000-5149 --arms react,reflexion,selfcons,planexec,rsos_01100 --design v3 --out phase3_staff.jsonl`
`python run.py --models (same) --family orders --seeds 3000-3149 --arms react,reflexion,selfcons,planexec,rsos_01100 --design v3 --out phase3_orders.jsonl`
Infrastructure errors are re-run by resuming (same command) before the analysis; rows still errored count as wrong.

## Hypotheses (one-sided exact sign tests on discordant paired units, α = 0.05)
- **H1 (primary):** rsos_01100 > react, pooled over models and families.
- **H2 (transfer across makers, only if H1 passes):** rsos_01100 > react within each model, Holm over the models.
- **H3 (against the stronger patterns):** rsos_01100 > reflexion, > selfcons, > planexec, pooled, Holm over the three.
- **H4 (cost, against selfcons):** tokens per correct answer, rsos_01100 / selfcons: 95 % bootstrap CI upper bound < 0.80,
  **and** accuracy difference rsos_01100 − selfcons: 95 % CI lower bound > −0.03 (10,000 resamples, seed 4242).

## What each outcome means (fixed now)
- H1 fails: the structure does not beat the default agent loop on new tasks and models. Reported as a negative.
- H1 + H2 on every included model: the structure chosen on one model transfers to models from other makers (blue,
  layer 1). With the layer-2 transfer results (turquoise) this is the first **cyan** candidate for the agents row.
- H3 per baseline: claimed only for the baselines that pass. H4: "as accurate as self-consistency at under 0.8× the
  cost" only if both parts pass.
- Expected from phase 1d (stated before the run, not a criterion): H1 and H2 likely; H3 vs selfcons and reflexion
  unlikely (phase 1d: 9/7 and 10/6); H4 likely on cost, uncertain on the accuracy bound.

## After phase 3
Results, roadmap colours by the rules above, then the τ-bench prediction (PLAN_TAU.md) with this structure, public
only on the owner's word.
