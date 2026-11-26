# Pre-registration A8: does blind planning hold across model families, model sizes and a stronger M\*? ($0)

Written 18 Nov 2026, 14:50 Kyiv, before any A8 model call. Source: pass 10 (`corpus/dragon_landings/`, sealed): each
limit of the A7 result is turned into a test that costs nothing. Harness: A7's (`a7_arms.py`, `a7_run.py`), unchanged
except for one new arm (B2s) and one new backend (`a7_openai.py`); replay checks pass with B2s on S1 and L3; the A7a
and A7b hashes are unchanged (42be52d5…, b1287a37…).

## Limits addressed, and how

| Limit of A7 | A8 test | Access, $0 |
|---|---|---|
| One model (Haiku 5.5) | **Claude ladder:** Sonnet 5.5 and Opus 5.5 (`A5_MODEL`) | owner's Claude plan, `claude -p` |
| One model family | **Other families:** any OpenAI-compatible free tier (e.g. Google AI Studio, Groq, Mistral, OpenRouter `:free` models) and local open models (Ollama) | free keys / owner's PC |
| Our M\* only | **B2s:** M\* told to work out the current value of every line a request reads, applying all earlier patches, before each patch | as above |
| Few M\* failures | the cells where M\* failed (S1, L3) run on every model | as above |
| Accounting cost | every result keeps per-call token counts; re-pricing from any price sheet is offline | — |

Cells per model: **S1** (14 steps, 30 keys) and **L3** (56 steps, 300 keys); arms **B2** and **X5b** on every model;
**B2s** on Haiku 5.5. Labels: `sonnet55`, `opus55`, `haiku_b2s`, `local_<model>`, `<provider>_<model>`. A model that
cannot complete a cell (quota, context) is reported as such, not dropped silently.

## Predictions (fixed now)

| # | Prediction | Pass if |
|---|---|---|
| **G1** invariance | blind planning stays exact on capable models | X5b ≥ 15/16 on every cell run with every Claude model and every free-tier model of ≥ 7B parameters or undisclosed size |
| **G2** error class | M\*'s errors are state-dependent on every family | pooled over all models, ≥ 90% of B2 and B2s failed steps are INHERIT/FUSE/SCALE/ROUTE/REHOST kinds, and X5b's failed steps ≤ 10% of B2's |
| **G3** cost | blind is cheaper per correct task at 300 keys on every priced model | X5b cost per correct ≤ B2's on L3 for Haiku and Sonnet (the sheets in `a5_prices.json`, api basis); Opus and free tiers reported in tokens |
| **G4** stronger M\* | telling M\* to track state does not close the gap | on Haiku, B2s exact ≤ X5b exact on S1 and L3, and B2s cost per correct ≥ 1.2× X5b's on L3 |
| **G5** families | no family where M\* is clearly better | on no model does B2 beat X5b by ≥ 2 exact tasks in a cell |
| P11 (A7c) | small local model | unchanged: X5b ≥ 12/16 on S1 where B2 on the same model ≤ 4/16 |

**REACH:** `REACH families ON limits.one_family TARGET 10 AGAINST one_family MEASURE model_families_with_blind_exact`:
the measured distance is the number of model families on which X5b stays exact.

## Analysis

`python experiments/a8_analyse.py` (0 model calls) → `results/a8.json`: per model, cell and arm, exact, failed steps
by kind, cost per correct (where priced), and G1–G5. Every failed prediction goes to the failure map.

**Amendment log (18 Nov 2026, after the Claude ladder, before any free-tier run counts).** `a7_openai.py` sends an
explicit `User-Agent: rsos-a8/1.0` and `Accept: application/json`. Groq's edge (Cloudflare) refused Python's default
`Python-urllib/3.x` agent with `HTTP 403, error code: 1010` on the owner's first smoke call; no task ran. Transport
header only; prompts, settings, arms and predictions are unchanged.

**Amendment 2 (19 Nov 2026, 00:10 Kyiv; before any run of Mistral, Gemini, Qwen, gpt-oss-20b or the local model, and
before the remaining gpt-oss-120b tasks).**
1. *Record correction.* Amendment 1's header text is wrong: the code sends
   `User-Agent: rsos-a8/0.3.1 (+https://github.com/r-a-elu-architecture/RSOS-Language)` and no `Accept` header
   (`a7_openai.py` at `9bc86a2`). Transport only; nothing else changes.
2. *Runner fix (committed in `9bc86a2`).* A provider error now stops one task, is logged to
   `results/a7_errors_<cell>_<label>.jsonl`, and is never written as a result; a rerun resumes the missing tasks. Before
   the fix, a 429 stopped result writing and tasks finished in parallel were lost and re-run. **Every first-run outcome
   in the owner's console log (`results/a8_groq_gptoss120b_console_run1.txt`) is reported, including X5b seed 302
   failed (1 step failed after retries, inv=3), whatever the rerun shows.** For G1 the cell counts the first
   completed outcome of each task.
3. *Providers.* Mistral La Plateforme (free Experiment tier) and Google AI Studio (free tier) run S1 and L3; Groq
   (gpt-oss-120b, gpt-oss-20b, qwen3.8-27b) runs S1 only (L3 requests exceed the free 8,000 tokens a minute: reported
   as not runnable, not dropped); qwen2.5:1.5b local runs S1 (A7c, P11). The exact model id is recorded in the label
   and the results; `-latest` aliases are not used.
4. *New predictions, fixed now.* They are scored only on runs that start after this amendment; the gpt-oss-120b S1
   tasks already seen (run 1 and run 2) are excluded from G6–G8.

| # | Prediction | Pass if |
|---|---|---|
| **G6** decoupling | blind exactness does not depend on the model; M\*'s does more | across all models of ≥ 7B run after this amendment, X5b's exact count per cell ranges over ≤ 1 task, and B2's range is larger than X5b's in at least one cell |
| **G7** immunity | the runtime stops every invalid operation before it acts, on every family | 0 invalid operations executed on any model (every proposed invalid operation rejected before execution, checked in transcripts), and the mean invalid operations proposed per X5b task on non-Claude models ≥ 3× the Claude mean (A8) |
| **G8** same request | M\*'s failures belong to the request, not the model | at least one B2 failed step on L3 (same seed, same step) fails on ≥ 2 non-Claude families and also failed on a Claude model in A8 |

REACH (instrument, not a threshold): families with X5b exact (target 10) and size span with X5b exact (target 100×,
1.5B to frontier).

**Amendment 3 (19 Nov 2026, 00:35 Kyiv; before any Mistral or Gemini run).** One named-step prediction (White Dragon
pass 12, Mendeleev landing). Basis (Claude, A7 + A8): M\* failed L3 seed 712 step 35 in 3 of 4 runs and L3 seed 702 step
35 once; base rate of M\* failure per REHOST request 1.4% (8 of 553).

| # | Prediction | Pass if |
|---|---|---|
| **G9** named step | M\*'s failure is fixed by the request before the model is chosen | on L3, B2 fails seed 712 step 35 or seed 702 step 35 on at least one of Mistral and Gemini, while X5b ends exact on both tasks on both families |

Chance level, if M\* failures landed on REHOST requests at random: about 5% (2 named of 54 REHOST requests per L3 run,
about 1.5 failures expected over the two families). A miss is recorded in the failure map as the named-step effect not
generalising.

**Amendment 4 (19 Nov 2026, 00:45 Kyiv; before any Mistral run).** Model ids listed by the owner's Mistral key
(00:41). The Mistral cell runs the pinned id **`mistral-large-4-0`** (label `mistral_large40`), S1 then L3, arms B2 and
X5b, `A7_WORKERS=2`, base `https://api.mistral.ai/v1`. The same key also lists `deepseek-v4-1-flash-1017` (DeepSeek),
`zai-glm-5-3` (Zhipu GLM) and `ministral-3b-2512` / `ministral-8b-2512` / `ministral-14b-2512` (a size ladder inside
one family); any of them run later only under the same cells, arms and predictions, labels `mistral_<id>`.
Price sheet fixed now (Mistral list price, sale ended 22 Oct 2026; USD per million tokens): mistral-large-4-0 input
1.36, cached input 0.14, output 4.18. The run is paid from the owner's Mistral plan credit; cost is reported per
correct task in USD and in tokens. Nothing else changes.

**Amendment 5 (19 Nov 2026, 01:00 Kyiv; after a failed start, before any Mistral task completed).** The first Mistral
call was refused: `HTTP 400 ... "top_p must be 1 when using greedy sampling"` (code 3054); 0 tasks ran. `a7_openai.py`
now sends `top_p: 1` with `temperature: 0`. With temperature 0 the sampling is greedy, and 1 is the default top_p on
OpenAI-compatible APIs, so outputs are unchanged on every provider. The owner's kit also had the runner from before the
fix (a provider error raised out of the run instead of stopping one task); the owner replaces `a7_run.py` and
`a7_openai.py` with the versions at this commit. Nothing else changes.

**Amendment 6 (19 Nov 2026, 01:35 Kyiv; before any Mistral task completed).** Second failed start: Mistral Large 4
returns `message.content` as a list of chunks (thinking, then text), and the backend passed the list on, so every task
stopped with `'list' object has no attribute 'split'` before any plan was parsed (logged in
`a7_errors_S1_mistral_large40.jsonl`; each cost one planner call, results 0). `a7_openai.py` now keeps only the `text`
chunks as the answer; a plain string answer is unchanged, so other providers are unaffected. Nothing else changes.

**Amendment 7 (19 Nov 2026, 01:50 Kyiv; analysis rule only, fixed while S1 runs and before any L3 result).** Mistral
Large 4 thinks far longer than Claude: the first nine S1 B2 tasks used 5,588–13,768 thinking tokens (seed 107 the most,
14,369 output tokens over 2 calls), against the 16,000 `max_tokens` cap fixed for every arm. The harness is not
changed. In the analysis, any call whose completion tokens are ≥ 15,900 (from the transcripts) is flagged
**cap-limited**; tasks with such a call are counted as the protocol counts them and are also reported separately, per
arm, so a failure caused by the cap is never read as a property of the method.

**Run note (19 Nov 2026, 03:30 Kyiv; Mistral L3 in progress, no result file seen yet).** The owner disconnected and
reconnected the drive holding the kit during L3. Nine B2 tasks (seeds 702, 704–711) stopped with `Errno 2` when writing
the transcript, after their model calls; no result or outcome was recorded or seen for any of them (console log
`results/a8_mistral_large40_console_run1.txt`). They are re-run from scratch by the resume command; the rerun is their
first observed outcome. B2 seed 702 is one of G9's two named tasks: its lost attempt has no outcome and is reported as
lost. Not a provider error, not a harness change.

**Amendment 8 (19 Nov 2026, 04:10 Kyiv; before any Gemini run).** Model ids listed by the owner's Google AI Studio key
(04:06). The Gemini cell runs the pinned id **`gemini-3.8-flash`** (label `gemini_38flash`), base
`https://generativelanguage.googleapis.com/v1beta/openai`, arms B2 and X5b, `A7_WORKERS=2`, **L3 first, then S1** (the
free tier's daily request limit is unknown; L3 decides G9). Project shown as free tier; the owner's prepaid credit
(EUR 5.84, auto-reload off) caps any charge. Cost reported in tokens. A cell cut short by the daily quota is reported
as incomplete with its completed tasks, never dropped. Nothing else changes.

**Amendment 9 (19 Nov 2026, 04:25 Kyiv; before any run on it).** A new backend, `a7_codex.py`: OpenAI models through the
Codex CLI (`codex exec --json`) on the owner's ChatGPT Pro plan, the counterpart of `claude -p` on the Claude plan
(owner, 04:08: "i have pro … if we can start now"). Same arms (B2, X5b), cells (L3 first, then S1), prompts, settings
the CLI exposes, retries and predictions; label `codex_<model>`. The CLI has no system field, so the system text goes
before the task text in the one message, for both arms alike; temperature is not settable through the CLI (reported).
Each call runs in an empty temporary folder with a read-only sandbox and the instruction to answer from the message
alone. **Any tool use** (shell command, file change, web search, MCP call) is recorded per call; tasks with any tool use
are reported separately and do not count for G1 or G9. Tokens from the CLI's usage events; cost reported as plan
(subscription) usage in tokens. The model id is pinned from the owner's CLI before the run and recorded here.
`a7_run.py`: `A7_BACKEND=codex` installs it and skips the Claude scaffold. Replay check S1 passes (0 model calls).

**Amendment 10 (19 Nov 2026, 04:50 Kyiv; before any Codex task).** Model list shown by the owner's Codex CLI
(`codex-cli 0.170.0`, ChatGPT Pro): GPT-6.2 Sol (marked current), GPT-6.2 Astra, GPT-6.1 Terra and older. The OpenAI
cell runs **`gpt-6.2-sol`** (the current default flagship) with the CLI's default reasoning level, label
`codex_gpt62sol`, `A7_WORKERS=2`, **L3 first, then S1**; the id is confirmed by one test call that is not a task.
The CLI reports no model in its events, so the id is pinned with `-m`. Token rule, fixed now: one null call
("Reply with the single word OK.") used 16,965 input tokens (13,952 cached), the CLI's own agent instructions; the
cost comparison is reported raw and with a per-call overhead subtracted, measured by 3 null calls before the run,
equally for both arms (as the Claude CLI scaffold in A5-A8). Tool use is excluded as in amendment 9. Nothing else
changes.
Amendment 10 note (04:47 Kyiv, before any Codex task): the owner's Codex menu shows the reasoning levels low, medium,
high, extra high; the default is **low**. The run uses that default (no level selected or passed); reported as
"GPT-6.2 Sol, reasoning low (CLI default)".

**Amendment 11 (19 Nov 2026, 04:55 Kyiv; before any Codex task; to be public before the run).** One more named-step
prediction, for a family not yet run on L3 (OpenAI, GPT-6.2 Sol through Codex, reasoning low).

| # | Prediction | Pass if |
|---|---|---|
| **G10** named step, OpenAI | the same request breaks the strongest one-call pattern on a fourth family | on L3, B2 fails seed 712 or seed 702 at step 35 on GPT-6.2 Sol, while X5b ends exact on both tasks |

Basis: step 35 of 712 failed on Haiku, Sonnet, Haiku B2s and Gemini; step 35 of 702 on Haiku B2s and Mistral; Opus,
the largest Claude model, passed both. Chance level as G9 (about 5% per family). A hit on 712 step 35 would also meet
G8 (Gemini and OpenAI). Tasks with tool use do not count (amendment 9).

**Amendment 12 (19 Nov 2026, 04:58 Kyiv; before any Codex task).** The owner's Codex install carries a plugin
(`superpowers`) whose skill makes the agent read skill files with a shell command before every answer; the first test
call ran `Get-Content` on a SKILL.md. The run therefore uses a clean Codex home (`CODEX_HOME` = a new folder holding
only the owner's sign-in and `config.toml` with `model_reasoning_effort = "low"`, the default the menu showed); no
plugins, skills or instruction files. Overhead measured by 3 null calls in that home with `-m gpt-6.2-sol`: 16,244
input tokens each (13,952 cached), 5 output, 0 reasoning, no tool items; this is the per-call overhead of amendment 10.
