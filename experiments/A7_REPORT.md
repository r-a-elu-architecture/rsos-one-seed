# A7a report: RSOS against M\* (one-call JSON Patch + audit), blind planning. 18 Nov 2026

Pre-registration: `experiments/PREREGISTRATION_A7.md` (no prediction changed, no amendment needed).
Analysis ran at commit `1ea545e` (harness code unchanged from `main`). Model Haiku 5.5, default thinking, `claude -p` on the session's OAuth login (owner approved this auth).
A7b (thinking off) and A7c are **not run** in this report.

## Strongest finding

**M\* nearly ties RSOS at this scale; the gap is 1.1–1.3×, not 2× or 10×.** B2 (the market's one-plan JSON Patch
pattern) was exact on 31/32 tasks against 32/32 for both RSOS arms. Its single failure is the result the experiment
was built to find: **S1 seed 107, step 13, a REHOST request** ("move bruno's services to chen"). B2 has to work out which
keys hold "bruno" from the state and write the literal values. It changed the wrong owner and missed two, and stayed wrong on both
retries even though the auditor named the exact error each time (3 attempts, 6 calls). The RSOS arms name keys and the runtime computes the
values, and they never failed. The mechanism is the one the prediction named, but with n = 1 it is a single event, not a rate.

**Blind planning works.** X5b saw no state values and was 32/32 exact, and was the cheapest arm per correct task on both sets.
The privacy property (plan without seeing the data) is available at no measured loss of exactness.

## Table (per task means; cost api basis, $ × 10⁻³ per correct task)

| Set | Arm | Exact | Calls | Input | Thinking | Invalid | Wrong | Failed | Cost/correct | Heal 0-call | ÷ B2 (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | B2 | 15/16 | 2.25 | 2261 | 1824 | 0 | 0 | 1 | 1.530 | 48/48 | |
| S1 | X5r | 16/16 | 2.375 | 2579 | 1715 | 4 | 0 | 0 | 1.251 | 48/48 | 0.818 (0.777–0.984) |
| S1 | X5b | 16/16 | 2.375 | 2428 | 1654 | 0 | 0 | 0 | 1.204 | 48/48 | 0.787 (0.787–0.899) |
| S2 | B2 | 16/16 | 2.0 | 2502 | 1820 | 0 | 0 | 0 | 1.433 | 48/48 | |
| S2 | X5r | 16/16 | 2.19 | 3025 | 1764 | 1 | 0 | 0 | 1.327 | 48/48 | 0.926 (0.853–1.018) |
| S2 | X5b | 16/16 | 2.25 | 2854 | 1734 | 4 | 0 | 0 | 1.304 | 48/48 | 0.910 (0.870–0.951) |

Scaffold removed: 571 tokens per call (6 null calls per set, `results/a7_scaffold.jsonl`).

## Verdicts

| # | Verdict | Measured |
|---|---|---|
| P1 runtime beats M\* | **FAIL** | X5r 16/16 on both sets ✓, but B2 15/16 and 16/16: never ≤ 13/16 |
| P2 blind costs no exactness | **PASS** | X5b 16 = X5r 16 on both sets |
| P3 cost per correct halves | **FAIL** | X5b ÷ B2 = 0.787 (S1), 0.910 (S2); target ≤ 0.5 |
| P4 blind input halves | **FAIL** | X5b input is **higher** than B2: 1.07× (S1), 1.14× (S2) |
| P5 M\* thinks ≥ 2× | **FAIL** | B2 ÷ X5b thinking = 1.10 (S1), 1.05 (S2) |
| P6 M\*'s errors on state-dependent steps | **PASS** (n = 1) | 1/1 B2 failed step is REHOST |
| P7 ≤ 3 calls per task | **PASS** (on the mean) | means 2.0–2.375; per-task maximum is 6 (B2 S1 107, X5b S1) and 5 (X5r S2) |
| P8 shared layer heals | **PASS** | 48/48 drifts healed at 0 calls, every arm, both sets |

**REACH cost_tenfold distance (B2 ÷ X5b cost per correct task):** S1 **1.271×**, S2 **1.099×** (target 10×).

## Error split by request kind

B2: 1 failed step, kind REHOST (state-dependent), 0 approved-wrong steps. X5r, X5b: 0 wrong, 0 failed. Invalid outputs
(X5r 4 + 1, X5b 0 + 4) were all repaired by retry within the same task; none reached the final state.

## Reading

- At 30 keys and 14 requests the state is small, so showing it costs little. That is why P4 fails: X5b's prompt carries
  the RSOS operation grammar, which is longer than B2's visible state. The value-free advantage can only show where
  state grows faster than the grammar. That is A7b's horizon/depth cell (P10), not this one.
- Thinking does not separate the arms with default thinking on (P5). The A5 cost gap from thinking came from B1's per-step
  protocol, not from what a planner has to compute.
- The single M\* failure is qualitatively different from everything RSOS did. An audit that names the error does not
  repair a value the planner must compute from the state. A runtime that computes the value removes that whole class of error.
  Measuring its rate needs the depth/horizon generator, where state-dependent steps dominate.

## Limits

n = 16 per set, one model, default thinking; S1/S2 are A5's generator at its original scale. The billing basis is
the session's OAuth login (`claude auth status`: "Claude API account"; no API key in the environment). The owner approved running on it.
Cost figures are A5's api basis, not an invoice.

## Hashes

| File | sha256 |
|---|---|
| `results/a7_default.json` (`results_sha256` field) | `42be52d5fbc82bfa2155129d832ebaeb13d4a31d79353be2db50f6eb54ad6d56` |
| `results/a7_default.json` (file) | `4829a81e492586ff38d3e3a6d370480ecf77a5f6543306174b2d795f79cfc661` |
| `results/a7_results_S1_default.jsonl` | `2ea5f92832d582cd8ace2d37c2e027dd1c8a1f24bbfde35d253272fba05d2d5c` |
| `results/a7_results_S2_default.jsonl` | `43c4287dc1ca4a55dc8846383300e7453cd6850cd632666fcfdb855fb6c11119` |
| `results/a7_transcripts_S1_default.jsonl` | `4548fb0db47c91febabb8acb8e0c65880c94b28029f8fba9352366fc1586160e` |
| `results/a7_transcripts_S2_default.jsonl` | `3cb92319a02c2bc56a11314824a520006208a035b3babf986396b22fc05419ed` |
| `results/a7_scaffold.jsonl` | `d9f319ae9ce9b818877aacdb0fec1b956fc2276aba9e94b14d800904f2613213` |

## A7b, thinking-off cell: **thinking control failed** (cell stopped, 18 Nov 2026)

Run: `A7_THINK=off python experiments/a7_run.py run S1` (48 tasks, all completed). The brief's check: thinking tokens
must be 0 in the off runs. **They are not: 0 of 48 tasks had 0 thinking tokens.**

| S1 arm | think/task, default | think/task, off | exact default | exact off |
|---|---|---|---|---|
| B2 | 1824 | 1833 | 15/16 | 15/16 |
| X5r | 1715 | 1762 | 16/16 | 16/16 |
| X5b | 1654 | 1807 | 16/16 | 16/16 |

**Cause, measured with 5 diagnostic calls:** `a7_arms.thinking("off")` does pass `MAX_THINKING_TOKENS=0` to each
CLI call (checked in process), but Claude Code 2.1.327 with `claude-haiku-5-5` ignores it. The same reasoning prompt
returned 62 thinking tokens with default settings, with `MAX_THINKING_TOKENS=0`, with
`--settings {"alwaysThinkingEnabled":false}` and with `--effort low`. No CLI control available in this session
turns thinking off for this model.

Per the brief, S2 off was **not run** and `a7_analyse.py off` was **not run**. P1b and P3b have **no verdict**: their
condition (thinking off) was never produced. The S1 off results are kept as a second default-thinking replicate,
not as A7b data: `results/a7_results_S1_off.jsonl`, `results/a7_transcripts_S1_off.jsonl`.

---

# A7b long tasks (L1, L2, L3; B2 and X5b; default thinking). 18 Nov 2026

Amendment of 13:40 in `experiments/PREREGISTRATION_A7.md`; no prediction changed, no code fix. Replay checks L1–L3
pass (0 calls). Smoke L2 seed 999: all three arms exact. X5r was not run on the long cells.

## Strongest finding

**Every planner failure in 96 long tasks is a value computed from state, and the runtime arm has none.** M\* (B2) had
7 failed steps in 6 of 48 tasks. All 7 are state-dependent kinds: **4 REHOST, 3 INHERIT**. Each stayed wrong through
2 retries while the auditor named the error. In 2 tasks the error reached the final state. X5b (blind; the runtime computes every value) had
**0 wrong and 0 failed steps over 48 tasks and about 5,400 steps**, and was exact on 48/48. Across A7a and A7b, B2's failed
steps total 8 of 8 on state-dependent kinds (A7a S1: 1 REHOST). The rate is low (2/48 tasks lost), which is why P9 fails.
The class of error is entirely on one side.

The cost gap widens with state size: X5b costs 0.68× (L1), 0.66× (L2), **0.50× (L3, 300 keys)** of B2 per correct task,
against 0.79×/0.91× in A7a.

## Table (per task means; cost api basis, $ × 10⁻³ per correct task)

| Cell | Arm | Exact | Calls | Input | Output | Thinking | Invalid | Wrong | Failed (dependent) | Cost/correct | Heal 0-call | X5b ÷ B2 (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L1 (56 steps, 30 keys) | B2 | 16/16 | 2.62 | 7256 | 9260 | 7039 | 0 | 0 | 2 (2) | 5.356 | 48/48 | |
| L1 | X5b | 16/16 | 2.50 | 7115 | 5887 | 4696 | 1 | 0 | 0 | 3.655 | 48/48 | 0.682 (0.632–0.738) |
| L2 (224 steps, chains of 16) | B2 | 15/16 | 2.88 | 25906 | 33745 | 25079 | 0 | 0 | 3 (3) | 20.761 | 47/47 | |
| L2 | X5b | 16/16 | 2.75 | 25164 | 22522 | 17342 | 0 | 0 | 0 | 13.777 | 47/47 | 0.664 (0.610–0.826) |
| L3 (56 steps, 300 keys) | B2 | 15/16 | 2.50 | 15631 | 13206 | 9788 | 0 | 0 | 2 (2) | 8.710 | 48/48 | |
| L3 | X5b | 16/16 | 2.00 | 10872 | 6546 | 4939 | 0 | 0 | 0 | 4.360 | 48/48 | 0.501 (0.472–0.603) |

## Verdicts

| # | Verdict | Measured |
|---|---|---|
| P9 on L2: B2 ≤ 8/16 and X5b ≥ 15/16 | **FAIL** | B2 **15/16**, X5b 16/16 (the X5b half holds) |
| P10: X5b input L3 ÷ L1 ≤ 1.5 and B2's ≥ 3 | **FAIL** | X5b **1.528** (misses by 0.028), B2 **2.154** |

**REACH cost_tenfold distance (B2 ÷ X5b cost per correct task):** L1 **1.465×**, L2 **1.507×**, L3 **1.998×**.

## Error split by request kind (B2; X5b has none)

| Cell | Seed | Step | Kind | Final state |
|---|---|---|---|---|
| L1 | 503 | 34, 43 | INHERIT, INHERIT | exact (overwritten later) |
| L2 | 601 | 196 | INHERIT | exact |
| L2 | 606 | 129 | REHOST | **wrong** (auth.owner, gateway.owner) |
| L2 | 609 | 123 | REHOST | exact |
| L3 | 711 | 36 | REHOST | exact |
| L3 | 712 | 34 | REHOST | **wrong** (11 keys, 8 of them owners) |

## Reading

- P9 assumed that long dependency chains break M\*. They do not: Haiku 5.5 tracks a 224-step chain in one plan with 15/16
  exact. What breaks it is REHOST (find every key with a given value, then rewrite them) and INHERIT (copy a value
  that earlier steps changed). The failure scales with the set the planner must scan (L3: 11 wrong keys in one task), not with
  chain length.
- P10: X5b's input grows 1.53× when the state goes 10× (30 → 300 keys) with no values shown. The growth comes from the
  key and service names it must name, not from values. B2 grows 2.15×, not 3×, because 56 requests dominate both
  prompts. X5b's advantage on input is real (0.70× of B2 at L3) but below the registered threshold.
- Thinking: B2 thinks 1.45–2.0× more than X5b on long tasks (A7a: 1.05–1.10×). The cost gap is mostly thinking and
  output, as in A5.

## Limits

n = 16 per cell, one model, default thinking (the thinking-off control is unavailable, see above). X5r was not run on
the long cells. Two lost tasks is too few for a rate. Billing basis as A7a (session OAuth login, owner-approved).

## Hashes

| File | sha256 |
|---|---|
| `results/a7_long_default.json` (`results_sha256` field) | `b1287a37560f98c06e58bddf2592b690b69a047862eea41cb37c90f228131016` |
| `results/a7_long_default.json` (file) | `c1d606e485929bc7bdc89787243c590dc2a0d2439cec7e704bee94318429b7a3` |
| `results/a7_results_L1_default.jsonl` | `ec1fbbff7335d23ed9d528d0e2c09abaef6493d2902f913ea82a5d363767e7a9` |
| `results/a7_results_L2_default.jsonl` | `b44639b6872326520b52240b9c4dad271e4979a6f6b135740fb59873dc30d9f1` |
| `results/a7_results_L3_default.jsonl` | `2421431c1501f5c845412fc778292f516e5a4a6379fdeeb00bfa6475ecba5ffc` |
| `results/a7_transcripts_L1_default.jsonl` | `eee271e18f3c4b0e881842c5e0d4e9d4da56a45f13277b9f1116eac7b326b1bb` |
| `results/a7_transcripts_L2_default.jsonl` | `633512cb67725a4ad88ed3f0dc295eaba9b65980874b497845604121cf3daa2b` |
| `results/a7_transcripts_L3_default.jsonl` | `b020cf3fad308b7d88020bb2e1c9ea845637dbfa94969e7783d623d28a24125a` |
| `results/a7_smoke_results.jsonl` | `6210c39ccc372db8b7210345654c5da0169abafe97f2764190d4c19e8bfba0d9` |
| `results/a7_smoke_transcripts.jsonl` | `e46fd750be6f5ad406381493a3a4aa2f680d054e2c0b7108b3b4719edde283eb` |
| `results/a7_scaffold.jsonl` | `7442d151e5803e02b18b556b50dd82780347b92d6fd9a87513bfe9648ebab35b` |
