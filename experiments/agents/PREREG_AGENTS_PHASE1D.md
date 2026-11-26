# Pre-registration: agents phase 1d (exploratory structure selection), 22 Nov 2026 ~12:45 Kyiv

The last harness retry allowed by PREREG_AGENTS_PHASE1C.md. Written after calibration 1c and before any call of 1d.
Sealed in SEAL_AGENTS_PHASE1D.txt. Everything in PREREG_AGENTS_PHASE1B/1C holds except the changes below.

## Calibration 1c result (calib1c.jsonl, commit abf74cf): REJECT, react 0.00 (0/20), 1 rate-limit error
Harness cause, from all 217 traces: **214 of 217 replies empty** (finish "stop", 60–145 characters of hidden reasoning,
no tool call returned). Renaming the tools did not help. Reading: gpt-oss forms a native tool call to the tools the
prompt describes; with no tools declared in the request, the provider returns nothing. The family was again not
measured. Under 1c's rule this is a harness cause, so this one retry is allowed; a further failure of the same kind
ends the orders family.

## Changes (design v3)
| Change | Reason |
|---|---|
| The task's tools are **declared natively** in every request of every tool-using arm (one string argument `args`); a returned tool call is rewritten to the same text action `ACTION: tool(args)` and appended to any text | the model's tool calls arrive instead of vanishing; all arms get the same declaration (plain: none, as before) |
| No reasoning-effort parameter (v2 had "low") | v1 (no parameter) worked in the OpenRouter smoke; v2 runs were the ones with mass empty replies |
| Reply 1500 tokens, task budget 16000 (as v2) | unchanged |
| Empty replies log the first 300 characters of hidden reasoning | diagnosis |
| **Plumbing check before the calibration** (emptycheck.py): orders seeds 1–3 (never used), arms react and rsos_11111; if more than 10% of replies are empty, STOP: no calibration | protects the last retry; not a gate on accuracy |
| Calibration on new seeds 940–959 | 900–939 were seen |

Unchanged: gate band 0.30–0.80 on react; phase seeds 2000–2099 (never run); 9 arms; decision rule.

## Steps (laptop)
1. `python run.py --models openrouter:openai/gpt-oss-20b --family orders --seeds 1-3 --arms react,rsos_11111 --design v3 --out smoke1d.jsonl`
   `python emptycheck.py smoke1d.jsonl`  → STOP: report and end. OK: step 2.
2. `python run.py --models openrouter:openai/gpt-oss-20b --family orders --seeds 940-959 --arms react --design v3 --out calib1d.jsonl`
   `python gate.py calib1d.jsonl`  → REJECT: the orders family ends (report). PASS: step 3.
3. `python run.py --models openrouter:openai/gpt-oss-20b --family orders --seeds 2000-2099 --arms all --design v3 --out phase1d.jsonl`
   `python select_structure.py phase1d.jsonl`  (best rsos arm ≥ react + 0.03, else STOP)

Phase 3 will use design v3 for every model, so the selection and the confirmatory test run on the same harness.
