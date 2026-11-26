# A5 Phase 0: cache diagnosis, price table, offline B1 (18 Nov 2026, before any task call)

Artefacts: `results/a5_cache_diagnosis.json` (30 probe calls, synthetic prompts and 12 recorded H-dragon prompts),
`results/a5_b1_offline.json` (0 calls), `experiments/a5_prices.json`, code `experiments/a5_llm.py`, `a5_cost.py`,
`a5_phase0.py`.

## 1. Why every A1–A4 call re-wrote its prefix (measured)

| Cause | Evidence |
|---|---|
| The CLI ran inside this remote session's environment and added the session's context (environment, scratchpad, proxy, attribution and account reminders) to every call | Null call: **1,349** tokens inherited environment vs **571** clean; the 12 recorded prompts cost **778.75** tokens more per call in the inherited environment |
| On a subscription the CLI writes with the **1-hour TTL** (2× input; Haiku 5.5 $0.20/MTok) | Legacy calls: 21,869 tokens written 1h, 0 at 5m; fixed calls: 0 at 1h, 12,524 at 5m |
| The agents' own static prefix (system prompt ≈ 20–120 tokens) is below the **512-token** minimum cacheable prefix, so no prefix is ever read | 0 tokens read on the 24 recorded-prompt calls (both modes). Threshold probe: the system region is read only once it is padded by ~60 notes (597 tokens read, then 867 at 90) |
| The CLI places the breakpoint at the end of the message, so the volatile part (request, state) is written every call | Every fixed call writes its whole message tail (~795 tokens in the probe) |

Recorded A4 sessions vs this session's legacy call: −26.3 tokens per call (same scaffold within 2%).

## 2. Fix (identical for every A5 arm)

Clean CLI environment (PATH, HOME, proxy and CA variables only), `FORCE_PROMPT_CACHING_5M=1`, no slash commands, no
MCP servers, static instructions moved into the system prompt (static first, request and state last). No arm has a
static prefix of 512 tokens, so caching cannot be read by any arm; the market-best accounting (basis `api`) bills
every content token at base input price and removes the CLI scaffold (571 tokens per call, measured), which a direct
API caller does not send.

Cost cross-check: the CLI's `total_cost_usd` equals tokens × the Haiku 5.5 sheet on all 30 probe calls (max
difference 1.1e-19 USD).

## 3. Price table (`a5_prices.json`, source platform.claude.com pricing page, fetched 18 Nov 2026)

Haiku 5.5 (run-time sheet): input $0.10, 5m write $0.125, 1h write $0.20, read $0.01, output $0.50 per MTok.
Alternative sheets: Sonnet 5.5 ($2 / $2.50 / $4 / $0.10 / $10), Fable 5.2 ($8 / $10 / $16 / $0.20 / $40). Batch −50%:
the A5 pipelines are sequential and do not qualify; a batch sensitivity scales every arm by 0.5 (ratios unchanged).

## 4. Offline B1 estimate (expected B1, committed before the live runs)

Recorded H-dragon transcripts (A3b S1 seeds 100–107, 300–307; A4 S2 seeds 400–415), content = recorded input −
recorded-session scaffold (1,322.7), output as recorded.

| Set | Calls | Content in | Out (planner / worker / checker) | As recorded | B1 cli (fixed call) | **B1 api (market best)** |
|---|---|---|---|---|---|---|
| S1 | 42.5 | 20,431 | 6,342 (3,153 / 768 / 2,421) | $0.016289 | $0.008758 | **$0.005214** |
| S2 | 42.4 | 19,302 | 4,551 (1,857 / 619 / 2,076) | $0.017235 | $0.007713 | **$0.004206** |

The fix alone: 1.86× (S1) and 2.23× (S2) on the CLI; 3.12× and 4.10× API-optimal. This is the market's gain and it
belongs to B1. K1's target per task on basis api: X3 ≤ **$0.000521** (S1), ≤ **$0.000421** (S2).
Output tokens are 61% (S1) and 54% (S2) of the api-basis B1 cost: after the fix, output (mostly planner and checker
thinking and prose) is the larger lever, not input.
