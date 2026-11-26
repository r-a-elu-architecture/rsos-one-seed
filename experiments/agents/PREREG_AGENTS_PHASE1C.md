# Pre-registration: agents phase 1c (exploratory structure selection), 22 Nov 2026 ~12:20 Kyiv

Written after the phase 1b calibration was rejected and before any call of phase 1c. Sealed in SEAL_AGENTS_PHASE1C.txt.
Everything in PREREG_AGENTS_PHASE1B.md holds, except the changes below.

## Phase 1b calibration result (calib1b.jsonl, commit b04a046): REJECT, react 0.05 (1/20), 0 errors
Cause, read from all 214 traces: **173 of 214 replies (81%) were empty**. gpt-oss treats tools named `find` and `get` as
its own built-in browser tool: 22 replies were native calls such as `repo_browser.find(shipped)` and
`repo_browser.get([1, ..., 10])`; the other empty replies are the same collision without a returned call. The family
was never measured; the gate did its job. My design error: tool names were not checked against the model's built-in
tools.

## Changes
| Change | Reason |
|---|---|
| `find` → `orders_where`, `get` → `order_details` (same behaviour) | no collision with gpt-oss built-in browser tools |
| Native tool calls with {"field","value"} or list arguments rewritten correctly; prefixes like `repo_browser.` dropped | the 1b rewrite produced `find(status, shipped)` |
| Empty replies log whether hidden reasoning or tool calls were present | diagnosis |
| Calibration on **new** seeds 920–939 | 900–919 were seen |

Unchanged: gate band 0.30–0.80 on react, design v2, phase 1b seeds 2000–2099 (never run), 9 arms, decision rule.

## Steps (laptop)
1. `python run.py --models openrouter:openai/gpt-oss-20b --family orders --seeds 920-939 --arms react --design v2 --out calib1c.jsonl`
   `python gate.py calib1c.jsonl`  → REJECT: stop and report. PASS: step 2.
2. `python run.py --models openrouter:openai/gpt-oss-20b --family orders --seeds 2000-2099 --arms all --design v2 --out phase1c.jsonl`
   `python select_structure.py phase1c.jsonl`  (best rsos arm ≥ react + 0.03, else STOP)

The gate may be used at most once more after this (phase 1d) for a harness cause; a REJECT for difficulty itself
(react genuinely below 0.30 or above 0.80 with under 10% empty replies) ends the orders family.
