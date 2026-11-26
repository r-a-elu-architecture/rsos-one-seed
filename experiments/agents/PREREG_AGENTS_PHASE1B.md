# Pre-registration: agents phase 1b (exploratory structure selection), 22 Nov 2026

Written after phase 1 stopped (RESULTS_PHASE1.md) and before any call of phase 1b. Sealed in SEAL_AGENTS_PHASE1B.txt.

## Changes from phase 1, and why
| Change | Reason |
|---|---|
| Selection family `orders` (tasks.py, family C): a hidden 30-order ledger; tools find (one condition), get (≤10 ids), calc | phase 1 hit the ceiling (plain 0.95 without tools); here the answer cannot be known without tools |
| Answers are never 0 | a guessed 0 must not score |
| Design v2: reply budget 1500 tokens, task budget 16000, reasoning effort "low" for gpt-oss and qwen3 on OpenRouter; native tool calls rewritten to text actions; lesson call up to 400 tokens | phase 1 had 0–13% empty replies |
| Difficulty gate (gate.py) | the family must leave room to help or hurt |

Unchanged: the 9 arms, 12 calls per task, the decision rule, the model.

## Steps (laptop, in this order)
1. Calibration (react only, 20 tasks):
   `python run.py --models openrouter:openai/gpt-oss-20b --family orders --seeds 900-919 --arms react --design v2 --out calib1b.jsonl`
   `python gate.py calib1b.jsonl`
   **REJECT** (react outside 0.30–0.80) → stop; phase 1b is not run; reported as such.
2. Phase 1b (only on PASS):
   `python run.py --models openrouter:openai/gpt-oss-20b --family orders --seeds 2000-2099 --arms all --design v2 --out phase1b.jsonl`
   `python select_structure.py phase1b.jsonl`
3. Decision (same rule as phase 1): the best rsos arm must reach react + 0.03, else **STOP**. Exploratory: it chooses the
   structure for phase 3 and is not evidence by itself.

## Phase 3 (planned, sealed separately after 1b)
Held-out family `staff` (new seeds) plus GSM8K, models openai/gpt-oss-20b, openai/gpt-oss-120b, qwen/qwen3.8-27b,
meta-llama/llama-4-scout; the chosen structure against each baseline, Holm, per model and pooled.
