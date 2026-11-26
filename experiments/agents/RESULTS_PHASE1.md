# Phase 1 result (exploratory, sealed in SEAL_AGENTS_PHASE1.txt): STOP

Run 22 Nov 2026, 11:27–11:47 Kyiv, openrouter:openai/gpt-oss-20b, warehouse seeds 1000–1099, 9 arms, 900 rows, 0
infrastructure errors. Data: `phase1.jsonl` (commit d280452).

| Arm | Accuracy | Mean calls | Mean tokens |
|---|---|---|---|
| reflexion | 0.97 | 2.2 | 976 |
| rsos_11110 | 0.96 | 2.0 | 862 |
| rsos_11111 | 0.96 | 2.3 | 1216 |
| selfcons | 0.96 | 3.4 | 1444 |
| react | 0.95 | 1.0 | 408 |
| plain (no tools) | 0.95 | 1.0 | 385 |
| rsos_11011 | 0.94 | 2.3 | 1094 |
| rsos_01100 | 0.94 | 2.1 | 932 |
| planexec | 0.63 | 2.3 | 1162 |

Sealed rule: best rsos arm (rsos_11111, 0.96) must reach react + 0.03 (0.98). It did not: **STOP**. The result stands.

## Cause (the fever principle: the signal is in the instrument)

1. **Ceiling.** `plain`, with no tools, scored 0.95: gpt-oss-20b does the warehouse arithmetic in its head; react used
   1.0 call on average (it answered without tools). 61 of 100 tasks were solved by all 9 arms. A +3-point gate on a
   0.95 baseline cannot measure a structure. My design error: the selection family was chosen for exact answers,
   without a difficulty check.
2. **Empty replies.** 0–13% of calls returned no text (planexec 13%, rsos_11011 13%, selfcons 10%): the hidden
   reasoning of gpt-oss used the 700-token reply budget. planexec's 0.63 comes mostly from this (example A1001: plan,
   two empty replies, then a wrong answer). The memory role's lesson call (120 tokens) was empty most of the time: only
   4 lessons were stored in 100 tasks.

Nothing here says the structure works or does not work in agents: the instrument could not tell.

## What follows (separately sealed: PREREG_AGENTS_PHASE1B.md)

A new selection family (orders: a hidden ledger reachable only through tools), a difficulty gate fixed in advance,
reply budgets that leave room for reasoning (design v2), new seeds. Phase 1 and its STOP are published together with
phase 1b, whatever 1b shows.
