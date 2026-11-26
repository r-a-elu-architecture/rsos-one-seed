# A3b pre-registration: the hologram palace (D90)

Written before any A3b code, dragon call or run (17 Nov 2026). Brief: `BRIEF_A3B_HOLOGRAM.md`. Owner's program: D90
with the 17:11 and 17:12 corrections (`corpus/chat-3/records/decisions.md`): the White Dragon lands on the palace's
door, walls, paintings and inside; the palace becomes a hologram, lighter and smaller, the tent about 5× its size;
opening the door restores the whole palace, everything the same. The dragon has no teacher: the tent (D) is only the
baseline it is measured against.

Files: harness `experiments/a3b_hologram.py` (new; imports `a1_agents.py` unchanged), dragon call
`experiments/a3b_dragon.py`, analysis `experiments/a3b_analyse.py`. Results: `results/a3b_hologram.json` (saved with
`common.save`, hash in the report), runs `results/a3b_runs.json` + `results/a3b_results.jsonl`, every message and LLM
call `results/a3b_transcripts.jsonl`, the dragon's design verbatim `results/a3b_dragon_design.json`.

## Host, tasks, drift (unchanged from A3)

Planner → worker → checker, all `claude-haiku-5-5` (headless `claude -p`, no tools), same system prompts, same
worker edit format (`SET` / `DEL` lines), same checker verdict format, max 2 retries. 30-line state, 14 change
requests, drifts at steps 4, 8, 12 (48 per condition). Seeds **100–107 and 300–307**. Smoke runs only on seed 999.

**Inside unchanged.** In both H arms every LLM prompt is byte-identical in construction to P's: the planner sees its
book, the worker sees the decoded instruction, its book and P's worker format, the checker sees request, decoded
instruction and the diff view of decoded changes on its own book. Every wire message must decode **exactly** to the
text P would have carried (instruction, reason, edits, state); the harness asserts the round trip on every message.
This is the owner's "if the door is opened … everything is there and the same".

## Re-use of A3's P, D and E

`a1_agents.py` is not modified (A3b code lives in new files). Before the report: (1) `git diff 8408a00 --
experiments/a1_agents.py` must be empty; (2) all 32 recorded A3 P and D runs are replayed through the current harness
(recorded outputs fed back, every prompt asserted identical) and must reproduce their A3 result records (success,
channel, billed, calls, drift). If both hold, A3's P and D are re-used (P 2,699, D 1,468 channel tok/task); otherwise
P and D are rerun live on all 16 seeds. E's recovery cost per healed drift (96.2 channel tok) is re-used from A3 for
B7 under the same check.

## Conditions

| | Designed by | Channel |
|---|---|---|
| P palace | A1 | as A3 (re-used) |
| D tent, Slipstream-style | A3 | as A3 (re-used) |
| **H-copy** | the brief's table (hand-built, fixed now) | below |
| **H-dragon** | the White Dragon, one call, before any H run | as the dragon specifies |

### H-copy (fixed now)

Out of band, once: the initial books (as P) and D's concept table (40 key anchors + 17 value anchors, 202 tokens,
reported once; excluded from the per-task channel as for D).

1. **Paintings + instruction (planner → worker):** `#<dot>` on line 1, then the instruction quantised with D's
   lossless anchor codec (`qenc`: keys → `Knn`, enumerated values → `Vnn`; raw text with `~` if not lossless).
2. **Walls, green dot:** `<dot>` = first **6 hex** of SHA-256 of the sender's whole book (P used 8). The leading dot
   on planner → worker lets the worker check its book before its LLM call; the trailing dot on worker → checker is the
   hash of the new state.
3. **Worker → checker:** the edits against the worker's book as anchors (`K08=3 K12=V03 -K20`, new lines in order),
   then ` =<dot of new state>`. The checker applies them to its own book and checks the dot; on mismatch it heals
   (A1 chunk heal) and decodes again, as P.
4. **Door, checker → worker:** `✓` on approve; on reject `✗ ` + the reason quantised with `qenc` (the worker needs the
   reason for its retry, exactly as in P).
5. **Checker → planner:** the approved worker message, unchanged (as P forwards it).
6. **Heal by reference (B7):** each agent keeps, besides its working book, the snapshot all three agreed at the last
   approval. On a leading-dot mismatch the worker restores every line where its working book differs from its
   snapshot, from the snapshot, and checks the dot again; if it matches it sends the notice `!k` (k = restored line
   numbers, comma-separated) to the planner. If it still does not match, the A1 chunk heal (`dragon_heal`) runs as in
   P. Drift injection (as A3): one untouched, format-valid line of the worker's **working** book; the snapshot is not
   touched (the same rule as E's acknowledged snapshot in A3).

### H-dragon (designed in one call, committed before any H run)

One call to `claude-opus-5-5` (as A2) with the White Dragon system prompt of A2. The prompt (fixed in
`a3b_dragon.py` before the call) gives: the host and its five places (door = checker → worker verdicts, walls =
green dots / hashes, paintings = keys inside messages, instruction = planner → worker, inside = the state), P's exact
current formats with one real example step from A3, A3's measured cost per place (instruction 1,349, edits 196, door
854, forward 187, heal 114 tok/task; palace integrity layer ~340), the tent's total only (1,468 tok/task; its formats
are not shown), the owner's target (≤ 0.2 × the tent), the metric (regex proxy + BPE guard + bytes, below), the
hard constraints (lossless decode to P's exact texts; LLM prompts unchanged; no extra LLM calls, codec = deterministic
code; drift detected before the worker's LLM call; every truncation detected; out-of-band only the initial books plus
fixed tables defined before the run, their one-time size reported; the codec may use any history both sides have
seen), the drift model, and a cross-domain library (holography, DNA coding and repair, error-correcting codes,
information theory and source coding, predictive coding, rocketry telemetry, double-entry bookkeeping, military
brevity codes, music notation, …). It returns landings (place, depth, order, domain, mechanism), an exact wire format
per edge with an example, its heal protocol, its tables, and **predicted channel tokens per task** (regex proxy,
total and per edge) and predicted integrity. The design is saved verbatim and committed before implementation; the
implementation follows it literally, and every deviation (anything unimplementable, ambiguous or breaking a hard
constraint) is listed in the report. The design is not revised after any H run.

## Measures

1. **Channel tokens per task**, A3's regex proxy (`\w+|[^\w\s]`), primary, for comparability with A3. **Guard
   against proxy artefacts:** the regex proxy counts any run of letters/digits as one token, so a dense encoding
   (base62 blob, long hash) would look free. Every message is also counted in **BPE tokens** (`tiktoken` o200k_base)
   and **bytes**; P and D are recounted the same way from the A3 transcripts.
2. LLM tokens billed, calls, wall-clock, cost; exact success; replica-consistent success; steps failed.
3. Drift per event as A3: healed, healed with 0 model calls, in the authoritative final state, in any copy at the end.
4. Recovery channel tokens per healed drift: the heal messages of that step (as P in A3).
5. **Truncation (offline):** every recorded worker → checker message of the H arms, tail cut 10–50% of characters
   (A3's fractions), decoded strictly by the receiver against the receiver's book recorded with the message, with the
   dot checked: detected / silently accepted wrong / correct. (A3's P check was only the dot's shape; H is checked
   with the full decode and hash.)
6. Offline: the cost of each H arm's heal if the snapshot had been corrupted as well (fallback heal size).

## Predictions (from the brief; B1–B4 and B7 for both H arms)

- **B1:** H channel tokens ≤ D's (1,468).
- **B2 (owner's target):** H channel tokens ≤ 0.2 × D's (≤ 293.6).
- **B3:** H keeps full integrity: 48/48 drifts healed with 0 model calls, 16/16 replica-consistent, 0 truncations
  silently accepted.
- **B4:** H exact successes ≥ D's (16).
- **B5:** H-dragon channel tokens ≤ H-copy's, with B3 holding for H-dragon.
- **B6:** H-dragon's predicted channel tokens per task within ±50% of measured.
- **B7 (R4 again):** H channel tokens per healed drift ≤ 0.25 × E's (96.2), i.e. ≤ 24.05.

**Validity rule for B1, B2, B5:** a pass on the regex proxy counts only if the same inequality also holds in BPE
tokens (D's BPE recounted from A3). Otherwise the result is reported as "fail (proxy artefact)".

## Expected weak points (written now)

- **B2 is very likely to fail for H-copy**, and is hard under the owner's own rule "everything the same": the
  planner's free-text instruction is ~75% of D's channel and must be restored exactly, so it can only be compressed
  losslessly. 0.2 × D is ~21 tokens per step, including the instruction.
- H-copy is D's formats plus the integrity layer; B1 depends on whether the bare `✓`, shorter headers and a 6-hex dot
  save more than the dots cost. Projection, not a result: ~1,300 tok/task.
- The reference heal relies on the untouched snapshot; with both copies corrupted it falls back to the chunk heal
  (~38 tok in A3), which would fail B7. Reported offline (measure 6).
- The dragon may propose mechanisms the harness cannot implement under the hard constraints; those are deviations,
  reported, not silently fixed.
- One model family, 16 tasks; P's and D's numbers come from the A3 batch (different day-time load), H from a new one.
