# A1 report: the first real-host test (three LLM agents, palace vs three baselines)

Pre-registration: `PREREGISTRATION_A1.md` (commit 9ef46bc, before any run). Code: `a1_agents.py` (harness, commit
of the run: the A1 harness commit), `a1_analyse.py`. Results: `results/a1_agents.json`, results_sha256
`d224abbf56c47013782b79a3f145c7b8863f61c6634ef43d27b68b10719732e1`; raw runs `results/a1_runs.json`; every
message and LLM call with its usage `results/a1_transcripts.jsonl`.

Host: planner → worker → checker, all `claude-haiku-5-5` (headless `claude -p`, no tools). 8 tasks (seeds
100–107) × 14 change requests on a 30-line state, 3 injected drifts per task (24 per condition). 32 task runs,
1,522 real LLM calls, total cost $0.79.

## Results (means per task)

| | P · palace | A · JSON full state | B · structured output | C · summaries + retrieval |
|---|---|---|---|---|
| Exact success | **7/8** | 5/8 | 5/8 | 0/8 |
| Wrong final lines per task | **0.125** | 0.375 | 0.375 | 4.75 |
| Line accuracy | **0.996** | 0.987 | 0.988 | 0.836 |
| Channel tokens (95% CI) | **2,563** (2,455–2,689) | 17,311 (16,922–17,652) | 24,425 | 4,561 |
| LLM tokens billed | **83,656** | 116,733 | 148,415 | 91,868 |
| billed, scaffold subtracted | **23,339** | 45,983 | 58,171 | 25,291 |
| Output tokens | **6,353** | 15,405 | 27,792 | 12,129 |
| LLM calls | **43.0** | 50.5 | 50.8 | 47.5 |
| Wall-clock (s) | **173** | 227 | 201 | 207 |
| Steps failed after 2 retries (all tasks) | 1 | 6 | 5 | 9 |
| Drift caught | **24/24** | **24/24** | 23/24 | 0/24 |
| Drift reaching the final state | 0 | 0 | 1 | 24 |
| Recovery per caught drift: channel tok | **38** | 875 | 1,607 | — |
| Recovery: LLM tokens billed / seconds | **0 / 0.00015 s** | 6,894 / 13.8 s | 10,214 / 13.0 s | — |

Truncation (offline, 10–50% of the tail cut from every recorded worker → checker message, strict decode): every
protocol detected 100% (P 580/580; A, B, C all detected because the cut JSON no longer parses). Recovery = resend
of that message: P 13 tokens, C 57, A 348, B 669.

## Predictions

| | Prediction | Result | |
|---|---|---|---|
| P1 | channel tokens P ≤ 0.5 × A at success ≥ A − 1 task | **0.148×**, success 7/8 vs 5/8 | Pass |
| P2 | drift caught P ≥ 95%, every baseline below P | P 24/24, but **A 24/24**, B 23/24, C 0/24 | **Fail** |
| P3 | heal ≤ 0.5 × full-state resend | **0.24×** (38 vs ~160 tokens) | Pass |
| P4 | billed tokens (scaffold subtracted) P ≤ 0.8 × A | 0.51× (raw 0.72×) | Pass |
| P5 | wall-clock P ≤ A | 173 s vs 227 s (0.76×) | Pass |
| P6 | truncation: P detects 100%, recovery ≤ 0.5 × A | 580/580; **0.037×** | Pass |

## Strongest finding

**On a real LLM host the palace is the only configuration that is cheap *and* correct at the same time.** The
two strong correctness baselines (A, B) keep the right state only by moving the whole state through every message
and by re-running the LLM when something drifts; the cheap baseline (C, the summary + retrieval memory pattern used
in production agent stacks) is light on the channel but silently kept **all 24 injected corruptions** and finished
**0/8 tasks** correct. The palace sits at C's cost (2,563 channel tokens, 0.56× of C) with better accuracy than A
(7/8 exact, 0.125 wrong lines per task, a third of A's).

The mechanism is visible in the recovery row: when a copy drifts, A and B spend a checker rejection plus a worker
regeneration (≈ 6.9–10.2k billed tokens, ≈ 13–14 s of LLM time); the green dot sees the drift before any LLM is
called and the White Dragon heal repairs it with 38 tokens in 0.15 ms, **zero LLM calls**. Drift handling moves
out of the model and into the protocol. That also explains the secondary gains: fewer calls (43 vs 50.5), half the
output tokens, 24% less wall-clock.

## What failed and what it means

- **P2 failed on the pre-registered wording.** A checker that remembers the last approved state catches drift as an
  "unrequested change" (A 24/24, B 23/24). Detection rate is therefore not where the palace is unique against a
  full-state baseline; **cost and determinism of detection are** (protocol check, no LLM judgement, 38 vs 875–1,607
  channel tokens, 0 vs 6.9–10.2k billed tokens). Against the memory baseline (C), detection itself is the
  difference: 24/24 vs 0/24.
- **Truncation detection is not a palace advantage** in this setting: strict JSON parsing also detects every cut.
  The advantage is the recovery size (13 vs 348 tokens). A lenient LLM-side parser would change this; not tested.
- The H3c filter decided 24/24 heals as "sender" (approved chain): the injected drifts were format-valid by design,
  so the filter reduced to restore. Measurability (real value for H3c): every line here carries a format test,
  100%, against the 60% H3c assumed.
- The palace's one failed task (seed 101, `search.tier`) was an LLM edit error that the checker rejected three
  times; the protocol did not cause it.

## Limits

One model family (no third-party keys in this environment; cross-family is open). Haiku-class agents, CLI-default
temperature, 8 tasks: the success differences (7 vs 5 of 8) are not statistically established; the token,
recovery and drift-in-C differences are large against their CIs. Channel tokens use the C1 regex proxy; billed
tokens are the API's own counts. The task is structured state editing, the case the palace is built for; free-text
collaboration is untested.
