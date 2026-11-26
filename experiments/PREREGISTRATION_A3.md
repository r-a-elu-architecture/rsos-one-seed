# A3 pre-registration: head to head against compact agent protocols

Written before any A3 code or run (17 Nov 2026). Brief: `BRIEF_A3_HEAD_TO_HEAD.md`. Harness: `experiments/a1_agents.py`
(A1's, extended with conditions D and E). Analysis: `experiments/a3_analyse.py`. Results:
`results/a3_head_to_head.json` (saved with `experiments/common.save`, results hash in the report), raw runs
`results/a3_runs.json`, every message and LLM call `results/a3_transcripts.jsonl`.

## Host and tasks (unchanged from A1)

Planner → worker → checker, all `claude-haiku-5-5` via headless `claude -p`, no tools, same role system prompts,
same worker edit format, same checker verdict format, max 2 retries. 30-line state, 14 change requests, drifts at
steps 4, 8, 12 (3 per task). Seeds **100–107** (A1's) and **300–307** (new, nothing tuned on them). All four
conditions are run fresh on all 16 seeds in one batch (64 task runs, 48 drift events per condition); the A1 numbers
are not reused.

## Conditions

| | Channel | Copies |
|---|---|---|
| **P palace** | exactly A1: `@state#hash` + instruction; worker → checker = line edits + trailing green dot `=hash`; White Dragon heal on any dot mismatch | each agent holds its own book |
| **A JSON full state** | exactly A1 (reference) | state travels in every message; checker keeps the last approved state |
| **D anchor protocol, Slipstream-style** | see below | each agent holds its own replica |
| **E delta protocol, ACCP-style** | see below | each agent holds its own replica |

D and E are **re-implementations from the published descriptions**, labelled "-style" everywhere. They are not the
original systems. Sources consulted: Slipstream (A. Maio, Zenodo preprints 2026, `slipcore` README: wire format
`SLIP v3 <src> <dst> <Force> <Object> [payload...]`, closed Force set incl. Request / Commit / Inform / Accept /
Reject, a shared Universal Concept Reference of anchors, claimed 82% token reduction); ACCP (draft-benzing-accp-00,
IETF individual draft, April 2026: per-session sequence numbers, ascending processing, gap → error SEQUENCE_GAP,
state sync as a version counter plus a delta of changed state). The full ACCP text could not be fetched from this
environment (mirrors returned 404/503), so E follows the brief's definition plus the search-level description; no
ACCP content hash is used because the brief specifies none and none was found.

### D: anchor protocol, Slipstream-style (design choices)

1. **Concept table agreed at the start** (out of band, like the initial books in P): every key of the task domain
   (5 services × 8 fields = 40 keys → `K00`–`K39`) and every enumerated value (6 owners, 4 regions, 4 log levels,
   3 tiers → `V00`–`V16`). Numbers stay literal. The table's one-time size is reported; the per-task channel
   comparison (R1) **excludes** it, as P's initial books are excluded (choice in D's favour).
2. **Wire format** `SLIP v3 <src> <dst> <Force> <Object> [payload]` with short agent ids `pl wk ck`:
   planner → worker `Request Edit <instruction>`; worker → checker `Commit Edit K07=3 K12=V03 -K20`;
   checker → worker `Accept Edit` or `Reject Edit <reason>`; checker → planner `Inform Edit <payload>`.
3. **Free-text payloads are quantised too:** every key and enumerated value inside the instruction and reasons is
   replaced by its anchor on the wire and expanded again by the receiver's SLIP layer before the LLM reads it
   (lossless; if a round trip ever failed, the raw text would be sent). The LLMs do exactly the same work as in P.
   This is the strongest compression the description allows without changing the agents (choice in D's favour).
4. The worker message carries the worker's **edits** (its new state against its own copy before the step), as
   intent payloads. **No hash, no heal, no state sync** (none in the description).
5. Error handling as A: the checker sees the decoded change on its own replica (same diff view as P) and approves
   or rejects; on reject the worker regenerates with the reason (max 2 retries). On approval each agent applies the
   edits to its own replica.

### E: delta protocol, ACCP-style (design choices)

1. Every message carries an envelope `ACCP s=<message seq>`; state messages carry `v=<base>><new>` version
   numbers. Receivers check the sequence (gap → reject) and that the base version equals their own version.
2. Worker → checker carries **only the lines changed since the last acknowledged version**: the diff between the
   worker's current working copy (after its edits) and the version the checker last acknowledged
   (`key=value`, `-key` for deletion). Checker → worker `ACK v=<n>` or `NAK v=<n>` + reason. On ACK the delta is
   forwarded to the planner with the same versions. Plain key names (no anchor table; none in the description).
3. **No content hash, no heal.** Same error handling as A: checker rejects, worker regenerates.
4. Consequence written now: a corruption of the worker's working copy shows up in E's delta as an unrequested change,
   so E can catch drift **only through the LLM checker** (model calls). In D the corruption never enters the channel:
   it stays as silent divergence in the worker's replica.

## Drift injection

As A1. P, D, E: one untouched, format-valid line of the **worker's own copy** is changed before the worker runs
(E: its working copy; its acknowledged snapshot is not touched). A: the state inside the planner → worker message.

## Measures (all four conditions)

1. Channel tokens per task (regex proxy as A1/C1) and bytes; D also with its one-time table.
2. LLM tokens billed per task, calls, output tokens, wall-clock, cost.
3. Exact success: the authoritative final state (P, D, E: the planner's copy, as in A1's P; A: the approved state)
   equals the truth. Also: **replica-consistent success** = every agent's copy equals the truth at the end.
4. Drift, per event: **healed** = at the end of the step every copy holds the true value of the corrupted line
   (A: the approved state). **Healed with 0 model calls** = the corrupted copy is already back to the true value
   before the worker's first LLM call of that step, i.e. repaired by the protocol alone. Also: drift present in the
   authoritative final state; drift present in any copy at the end.
5. Recovery cost per healed drift: channel tokens (heal messages for P; for A, D, E all messages of attempts ≥ 1
   plus the reject messages, as A1) and LLM tokens billed (calls of attempts ≥ 1 at that step; P: 0).
6. Secondary, offline (no prediction): truncation of the recorded worker → checker messages (tail cut 10–50% of
   characters), strict decode by each protocol: detected / silent wrong / correct.

## Predictions (fixed now, from the brief)

- **R1 channel tokens:** mean P ≤ 1.2 × min(mean D, mean E).
- **R2 drift:** P heals 48/48 with 0 model calls; D and E each heal **fewer than P** with 0 model calls.
- **R3 success:** P exact successes ≥ D and ≥ E (authoritative definition).
- **R4 recovery:** P's tokens per healed drift ≤ 0.25 × D's and ≤ 0.25 × E's. Passes only if it holds both for
  (a) channel + billed LLM tokens and (b) channel tokens alone. If D or E heals no drift at all, R4 is **undefined**
  for that condition and is reported as such, not as a pass.

## Expected weak points (written now)

- D will probably never heal drift, and it will probably also never *see* it: its authoritative state can stay
  correct while the worker's replica is silently wrong. R3 (authoritative) may therefore tie; replica-consistent
  success is where the difference should show. Both are reported.
- D's quantised channel may be smaller than P on the forward path: P carries an 8-hex hash per message and full
  JSON verdicts with reasons (A1 format, unchanged); D sends bare `Accept Edit`. R1 allows P 1.2× and may fail.
- E's recovery channel is small (a short NAK plus a short delta), so R4(b) may fail even if R4(a) passes.
- One model family, 16 tasks, CLI-default temperature.

## Amendment 1 (17 Nov 2026, before the main run; after one smoke run per condition on seed 999, not a test seed)

Smoke run E, seed 999, step 4: the corrupted line (`auth.retries` 7 → 0) appeared in E's delta, the checker
rejected it three times naming the change, and the worker re-sent the same delta each time: its prompt showed only
its (corrupted) state, so it could not see that its outgoing message carried the line. The step failed, and so did
step 5. Because the brief says "no strawmen", the D and E workers now also receive, on a retry, the line changes
their rejected message carried (E: "since the last acknowledged version"). This is information the sending side of
each protocol already holds. It favours D and E. P and A are unchanged. Predictions, measures and seeds are unchanged.
Smoke numbers (seed 999, before the amendment): P success, 2,489 channel tok, 42 calls; D success, 1,300 channel
tok, 42 calls, 0/3 drift healed, 3/3 latent in the worker's replica; E failure (acc 0.833), 3,466 channel tok,
80 calls.
