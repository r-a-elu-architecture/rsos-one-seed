# Pre-registration A5: the model bill, 10× below the market's best setup

Written 18 Nov 2026 after Phase 0 (`experiments/A5_PHASE0.md`, commit a774fc5) and before any A5 arm code or task
call. Brief: `experiments/BRIEF_A5_COST.md`. Branch: `claude/zen-bell-cvute6` (this session's assigned development
branch; the brief's `claude/a5-cost` role). Frozen files are imported, never edited: `a1_agents.py`, `a3_run.py`,
`a3b_hologram.py`, `a3b_hdragon.py`, `a3c_*.py`, `a4_*.py`. New code: `a5_*.py`.

## 1. Host, model, call

Every call of every arm: `claude -p`, model `claude-haiku-5-5`, default thinking and effort (as A3b and A4), the
Phase 0 fixed call (`a5_llm.py`: clean environment, 5-minute TTL, no slash commands, no MCP servers). Static
instructions live in the system prompt; request and state come last. Up to 4 transport retries per call (as A1).
Haiku 5.5 is the cheapest current model, so the brief's secondary arms X4 and B1r (a smaller model on simple steps)
have no smaller model to route to: **not run, recorded as not applicable.**

## 2. Task sets (no tuning on test seeds; smoke only on seed 999)

- **S1:** A3's generator (`a1_agents.make_task`, unpatched), seeds 100–107 and 300–307, drift at steps 4, 8, 12.
- **S2:** A4's generator (`a4_latent.patch()`: compute-from-copy requests, A4 planner and checker prompts), seeds
  400–415, drift at steps 4, 8, 12 on keys that six later requests read.

## 3. Arms (16 tasks per set each)

**B1, market best.** H-dragon exactly as in A3b (S1) and A4 (S2): `a3b_hologram.run_task(HDragon())` (S2 through
`a4_latent.run_one`), with the fixed call. The only change: the static output instruction at the end of the worker
(`W_P`) and checker (`C_OUT`) prompts is moved to the end of the system prompt (text unchanged; static first).

**X arms: the model decides, the language executes.** One loop (`a5_arms.py`), same integrity layer as B1 (three
copies: planner, worker, checker; drift injected into the worker copy at the same steps with the same values; before
every step the runtime compares each copy's green dot with the agreed snapshot and restores a drifted copy from the
snapshot, 0 model calls; after every step all three copies must carry one dot). Per step:

1. **Planner call** translates the change request into RSOS operations (grammar below). The planner never looks up
   or computes a value: the runtime does. No parser written for the task generator is used anywhere in an arm.
2. **Runtime** parses the operations, checks validity (grammar; referenced keys exist; DEL of an existing key;
   every written line matches its field format), executes them on each of the three copies independently and
   requires the three results to be identical (compute re-derivation). Invalid → the planner is called again with
   the runtime's error (counts as an attempt).
3. **Audit call** (when the rule below selects the step): the checker model receives the request, the operations
   and the runtime's result (changed lines old → new, and the values of the source lines the operations read) and
   answers `ok` or `no: <reason>`. `no` → the planner is called again with the reason.
4. Up to 3 attempts per step (A1's MAX_RETRY = 2). No approval → the step fails and the state is unchanged.

RSOS operations (one per line; key = `service.field`, or its palace code in X3):

| Operation | Effect |
|---|---|
| `SET k v` | k = v (appended at the end if k is new) |
| `DEL k` | remove line k |
| `INHERIT d s [+n] [CAP m]` | d = s (+ n), at most m |
| `FUSE d a b [CAP m]` | d = a + b, at most m |
| `SCALE k f [CAP m]` | k = k × f, at most m |
| `ROUTE s = x : d v1 \| v2` | d = v1 if s equals x, else v2 |
| `REHOST field a b` | every line of that field whose value is a becomes b |

| Arm | Planner writes | Planner sees | Audit |
|---|---|---|---|
| **X1** language executes | its prose instruction (as B1), then `---`, then the operations | the full state (as B1) | every step |
| **X1s** sampled audit | as X1 | as X1 | risk-weighted + 1 in 4 |
| **X2** RSOS out | operations only | the full state | as X1s |
| **X3** RSOS in | operations only | the request and only the state lines it names, in palace notation | as X1s, prompt in palace notation |

**Audit rule (X1s, X2, X3), fixed now.** A step is audited if its operations contain any of `DEL`, `INHERIT`,
`FUSE`, `SCALE`, `ROUTE`, `REHOST`, or execute to no change; otherwise it is audited iff
`int(sha256("<set>:<seed>:<step>"), 16) % 4 == 0`. The class is read from the planner's operations, never from the
request. Every attempt of a selected step is audited.

**Palace notation (X3).** Each line is written as its two-letter palace code and value (`at=700`: service letter
a b s c g, field letter r t y o g l m e, the A3b H-dragon table); the legend is in the static system prompt; values
of region use the full name. **Line selection (X3), generic:** a state line is shown if the request contains its full
key, or both its service name and its field name, or (for a non-numeric value) its value as a word. Audit prompts in
X3 carry only the changed lines and the source lines, in palace notation.

## 4. Cost model (fixed now; `a5_cost.py`, `a5_prices.json`)

Cost per task = Σ over calls of tokens × price, by class. Two bases:

- **api (primary, market best):** the CLI scaffold removed and every remaining input token at base input price;
  output as measured. The scaffold is the mean input of 3 null calls (fixed call) at the start and 3 at the end of
  each set's run. No arm has a static prefix of 512 tokens, so no arm can read the cache on the API either.
- **billed (secondary):** exactly as the CLI billed it (input, 5m and 1h writes, reads, output).

Sheets: run-time `haiku-5-5`, alternatives `alt-sonnet-5-5`, `alt-fable-5-2`. Batch: not applicable (sequential);
sensitivity ×0.5 for every arm.

## 5. Predictions

| | Prediction | Pass rule |
|---|---|---|
| **K1** (owner's target) | X3 cost ≤ 0.1 × B1 | mean cost per task, basis api, run-time sheet, on S1 **and** S2; valid only if it also holds under both alternative sheets, else "fail (price-dependent)". Basis billed reported with its own verdict |
| **K2** | X1s model calls ≤ 0.4 × B1 | mean calls per task, on each set |
| **K3** | X2 output tokens ≤ 0.25 × B1 | mean output tokens per task (thinking included), on each set |
| **K4** (non-inferiority) | X3 exact ≥ B1 exact − 1, and X3 replica-consistent 16/16 | on each set |
| **K5** | S2: X3 drift-traced wrong values = 0 | A4's class: final target value equals the value computed from the drifted source |
| **K6** | offline B1 estimate within ±25% of live B1 cost | basis api, run-time sheet, on each set ($0.005214 S1, $0.004206 S2) |

## 6. Measures (all arms)

Cost per task by role and by token class; model calls; billed tokens; exact success (planner copy = truth);
replica-consistent success (all three copies = truth); drift healed with 0 model calls; S2 compute classes (correct,
traced, other wrong); for X arms: invalid operations, audit verdicts, audit misses (a step whose executed operations
differ from the truth transition and that the audit approved, or that was not sampled), step failures; wall-clock;
channel tokens (regex and BPE, tiktoken o200k_base; the planner → runtime operations message, the runtime → auditor
message and the verdict for X arms; A3b's wire messages for B1). Bootstrap 95% CIs (common.bootstrap_ci) on cost
ratios.

## 7. Procedure

1. Replay check before any live call: the 16 A3b and 16 A4 H-dragon transcripts replayed through the frozen code and
   through A5's B1 wiring reproduce every recorded field (0 mismatches); frozen files unchanged against `main`; the X
   runtime given correct operations by a test-only oracle reaches the truth on all 32 tasks (oracle not used by any
   arm).
2. Smoke: one task of every arm on seed 999 (S1 and S2 generators). Smoke may fix code bugs; prompts and rules change
   only by a numbered amendment committed before the live runs.
3. Live: all arms, both sets, resumable runner, 8 parallel workers, commit after each set.
4. Report `experiments/A5_REPORT.md` with exact numbers, every audit miss, and every failed prediction.

## 8. Expected weak points (from the brief, kept)

Wrong or invalid operations missed by the sampled audit; output (thinking) dominates cost after the fix, so K1 may
fail even with zero workers; removing the worker removes a second reading of the request; one model family, 16 tasks
per set.

## Amendments (committed before the live runs; smoke 1 on seed 999 only)

Smoke 1 (S1, seed 999, all five arms, `results/a5_smoke_results.jsonl`): all 5 exact; API-basis cost B1 $0.003657,
X1 $0.003579, X1s $0.003207, X2 $0.001967, X3 $0.002760. The X planners' static system prompt (role + grammar,
~300 tokens) and their thinking (X1 planner 2,402 thinking tokens vs B1 planner 823) dominate; X3 had 7 invalid
outputs (palace `code=value` inside operations, a field letter in REHOST, a prose line).

**Code fixes (parser, all X arms):** `SET k=v` and `SET k = v` accepted; palace field letters accepted in REHOST;
lines that do not start with an operation keyword are skipped and counted (`a5_arms.SKIPPED`). Semantics unchanged.

**Amendment 1 (prompt, all X arms):** the grammar text is rewritten compactly (same seven operations, same meaning;
`GRAMMAR_V0` kept in the code for the record).

**Amendment 2 (new secondary arm X5, the assembly line; pass 4 planet 5):** X3 with all 14 requests of a task in one
planner call (each request with its selected lines from the initial state; output `#<n>` + operations) and the audit
of every selected step in one auditor call (`<n> ok` / `<n> no: <reason>`); same audit rule. Up to 3 rounds: invalid
or rejected steps are re-planned together (one call) and re-audited; the runtime re-executes the whole task each
round (drift and heal included, 0 calls). Steps not approved after round 3 are left out. A correction can change the
result of a later, already approved step; that step is not re-audited (its operations are state-independent), and
every such case appears in the audit-miss count if its result is wrong. **K1 is still judged on X3.** X5 is reported
as a secondary ratio (X5 / B1, basis api, three sheets) with the same K4 and K5 checks, labelled secondary.

Replay check re-run after these changes: both sets pass (B1 32/32, 0 mismatches; oracle 80/80 per set including X5 at
2 calls per task). Smoke 2 (seed 999, all six arms, S1 and S2) follows; no further prompt change without amendment 3.

### Smoke 2 and amendment 3 (before the live runs)

Smoke 2 (seed 999, six arms, both generators): B1, X2 (S1) and X5 (S1, S2) exact; X1, X1s, X3 (S1) and X1, X1s,
X2, X3 (S2) not exact. API-basis cost: S1 B1 $0.004816, X5 $0.001418; S2 B1 $0.004526, X5 $0.001535. Causes, all
read from the step logs: (a) the auditor did not see the before-values, so it rejected a correct `SET gateway.owner
alice` for "everything owned by emeka" and every no-change result (it could not see the prior value); (b) the planner
wrote copies of non-numeric values as `SET d s` or left them out, reading INHERIT as numeric; (c) the auditor
sometimes reasoned first and never began with `ok` (parsed as a rejection).

**Code fixes:** the verdict is the last line that begins with `ok` or `no`; `SET d s` with an existing key as value
executes as a copy and is audited as a risk step; stored audit text kept to 1,500 characters (was 300).

**Amendment 3 (prompts, all X arms including X5):** the grammar adds "INHERIT copies any value (numbers, owners,
regions, levels)"; every audit prompt adds the before-values of the lines the request names (the same generic
selection as X3) and of the lines the operations name (X3, X5 in palace notation). Smoke 3 on seed 999 follows; the
live runs start after it whatever its outcome, with no further change.

### Smoke 3 (seed 999) and the last code fix

Smoke 3: 10 of 12 exact (S1: B1, X1, X1s, X2, X3 exact, X5 not; S2: B1, X1, X2, X3, X5 exact, X1s not). API-basis:
S1 B1 $0.003572, X3 $0.002917, X5 $0.001691; S2 B1 $0.004525, X3 $0.002760, X5 $0.000947. X5 S1 lost step 13: the
auditor answered a one-step re-audit as `1. ok` (list position) and the parser looked for `13`. **Code fix:** when no
verdict carries an audited step's number and the verdicts are numbered 1..m for m audited steps, they are mapped by
position. No prompt or rule change. Live runs follow.
