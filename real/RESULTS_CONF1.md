# RESULTS CONF1 (sealed; analyze_conf1.py exactly as PREREG_CONF1.md)

**LEVEL: UNPRECEDENTED** (4 of 4 domains pass; untraced families: 0).

| Row | Model | Standard | Full seed vs standard | pass | Full seed vs strongest | Generated vs standard | pass | Generated vs full seed |
|---|---|---|---|---|---|---|---|---|
| ai_agents | openrouter:openai/gpt-oss-20b | react | +58.0 % tokens, result +0.113 (38/40), Holm p=8.46e-11 | YES | +75.2 % tokens, result +0.037 (40/40), p=1.55e-20 | -0.4 % tokens, result +0.000 (21/40), Holm p=5.42e-01 | no | -139.2 % tokens, result -0.113 (1/40), p=1.00e+00 |
| ai_agents | openrouter:openai/gpt-oss-20b | selfcons | +68.8 % tokens, result +0.150 (40/40), Holm p=5.47e-27 | YES | +56.8 % tokens, result +0.081 (39/40), p=4.45e-16 | +47.5 % tokens, result -0.019 (40/40), Holm p=5.55e-26 | no | -68.5 % tokens, result -0.169 (4/40), p=1.00e+00 |
| ai_human | openrouter:mistralai/mistral-small-3.2-24b-instruct | std | +41.6 % tokens, result +0.218 (38/38), Holm p=4.85e-21 | YES | – | +0.8 % tokens, result +0.092 (29/38), Holm p=6.83e-03 | no | -69.8 % tokens, result -0.126 (0/38), p=1.00e+00 |
| economics | - | std | +1.42 % (12/12), Holm p=1.13e-09 | YES | +0.00 % (5/12), p=4.98e-01 | – | – | – |
| space | - | std | +1.67 % (12/12), Holm p=1.39e-09 | YES | +1.33 % (12/12), p=1.66e-03 | – | – | – |

Domains: ai_agents: PASS, ai_human: PASS, economics: PASS, space: PASS
Generated arm (secondary): ai_agents: no, ai_human: no

## Operator trace (families the full seed chose -> RSOS operator)

| Row / family | Uses | Kind | Operator |
|---|---|---|---|
| ai_agents|F:blind-b0 | 288 | lever | compress |
| ai_agents|F:blind-b1 | 109 | lever | compress |
| ai_agents|F:blind-b2 | 4 | lever | compress |
| ai_agents|F:reuse-b0 | 27 | lever | inherit |
| ai_agents|F:reuse-b1 | 4 | lever | inherit |
| ai_agents|P4P5-cges | 5 | lever | fuse |
| ai_agents|focus-b0 | 6 | native | beam |
| ai_agents|open | 5 | native | explore |
| ai_agents|stop | 126 | native | no mapping |
| ai_human|F:holo-top | 33 | lever | compress |
| ai_human|F:holomin-top | 212 | lever | compress |
| ai_human|top | 20 | native | fuse |
| ai_human|unit-0 | 33 | native | beam |
| ai_human|unit-0c | 1 | native | beam |
| ai_human|unit-1c | 1 | native | beam |
| ai_human|unit-2 | 1 | native | beam |
| economics|F:otrace:lp_corrected | 18 | lever | heal |
| economics|F:pool:capital_newsvendor | 13 | lever | fuse |
| economics|P4P5:stochastic_lp | 276 | lever | fuse |
| economics|focus_big | 1 | native | beam |
| space|F:holo-carry | 152 | lever | carry |
| space|F:holo-plan | 89 | lever | carry |
| space|P1:counter-shift | 1 | lever | heal |
| space|P3:repair-partial | 1 | lever | heal |
| space|P4P5:exact-planner | 17 | lever | fuse |
| space|focus_science | 14 | native | beam |
