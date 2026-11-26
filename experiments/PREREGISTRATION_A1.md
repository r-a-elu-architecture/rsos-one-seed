# A1 pre-registration: the first real-host test (AI agent workflow, D68)

Written before any run. Brief: `BRIEF_A1_AGENT_TEST.md`. Code: `experiments/a1_agents.py`. Results:
`results/a1_agents.json` (+ `results/a1_transcripts.jsonl`, every message and every LLM call with its usage).

## Host

Three real LLM agents, **planner → worker → checker**, sharing one multi-step task. No third-party API keys are
set in this environment, so all agents are **Claude instances** (`claude-haiku-5-5`, called headless through
`claude -p`, no tools, own system prompt per role, temperature at the CLI default). Cross-family is not tested.

## Task set (fixed, seeds 100–107)

Each task = a shared **state** of 30 configuration lines (`service.field = value`) and **14 change requests**
in natural language (set a value, rename a key, add a line, delete a line, conditional "if X then Y"). The
generator (`make_task(seed)`) computes the true final state, so success has exact ground truth.

Per step: planner reads the request and its view of the state and writes an instruction; worker applies it;
checker verifies that only the requested change was made (it keeps the last approved state) and approves or
rejects with a reason; on reject the worker retries (max 2 retries). 14 steps × 3 roles = 42+ messages per task.

## Conditions

| | Channel between agents | What each agent sees |
|---|---|---|
| **P · RSOS palace** | `@state#hash` + line edits + trailing green dot `=newhash` (`rsoslang.palace`); planner → worker carries `@state#hash` + instruction | each agent holds its own copy of the book |
| **A · JSON full state** | JSON `{instruction | note, state: full}` every message | the state in the incoming message |
| **B · structured output** | worker/checker output via `--json-schema` (function calling); state as typed array | as A |
| **C · summaries + retrieval** | summary text + key writes; a shared memory store; receivers retrieve the top-8 lines relevant to the message (keyword overlap) | retrieved lines only |

P specifics: green-dot check on every message; on mismatch the **White Dragon heal** (chunk hashes, only the
differing chunks travel, `palace.heal`) instead of a resend. Which chunk version is kept follows the H3c filter:
drop a version that fails the line-format test; of the rest keep the version on the approved hash chain (the
planner's). A trailing-dot mismatch after decode (e.g. truncation) is also healed.

## Injected drift (known ground truth)

At steps 4, 8 and 12 of every task (24 events per condition), before the worker runs, the harness silently
changes one line not touched by the current request to another **format-valid** value, in what the worker sees:
P: the worker's own book; A/B: the state inside the planner → worker message; C: the shared store.
**Caught** = the corrupted line is back to the true value when the step is approved. **Silent** = it reaches the
final state.

## Measures

1. Channel tokens per completed task (sum over all inter-agent messages; regex token proxy as in C1, plus bytes).
2. LLM tokens billed (input incl. cache + output, from the CLI usage) per task; also with the per-call fixed
   scaffold subtracted (scaffold measured by a null call with the same flags).
3. Task success: final state exactly equal to the truth; also line accuracy.
4. Drift caught / silent; recovery tokens and seconds from detection to restored line.
5. Truncation tolerance (offline, on the recorded worker → checker messages): cut the last 10/20/30/40/50% of
   characters; outcome = detected / silent wrong / correct; recovery cost (tokens) if detected.
6. Wall-clock per task.

## Predictions (fixed now)

- **P1** channel tokens per task: P ≤ 0.5 × A, with exact-success rate P ≥ A − 12.5 points (one task).
- **P2** drift caught: P ≥ 95% (≥ 23/24); every baseline below P.
- **P3** recovery cost: P heal tokens ≤ 0.5 × the full-state resend (C1 found 0.36×).
- **P4** LLM tokens billed per task, scaffold subtracted: P ≤ 0.8 × A.
- **P5** wall-clock per task: P ≤ A.
- **P6** truncation: P detects 100% of truncated messages and its recovery costs ≤ 0.5 × A's.

## Expected weak points (written now so they cannot be explained away later)

- C is strong on channel tokens too (it sends writes, not state); P1 is against A, but C will be reported.
- A/B checkers keep the previous approved state, so a careful LLM checker can catch drift as an unrequested
  change: baselines may catch some drift. P2 says only that P is higher.
- One model family, temperature not controllable, 8 tasks: small sample, reported with exact counts.
