# RESULTS CONF2 (sealed; analyze_conf2.py exactly as PREREG_CONF2.md; CONF1 + CONF2 outputs)

- **Claim 1, cross-domain seed: STRONG** (4 of 5 rows at Holm p < 1e-5)
- **Claim 2, communication principle: STRONG** (2 of 3 rows at Holm p < 1e-7, equal or better result)
- **Claim 3, operator language (generated moves): NOT SHOWN** (0 of 4 rows at Holm p < 1e-5)

| Row | Standard | Full seed vs standard (claim 1) | Tokens (claim 2) | Generated vs standard (claim 3) | Full seed vs strongest | Generated vs full seed |
|---|---|---|---|---|---|---|
| ai_agents | react | +58.0 % tokens, result +0.113 (40 cells), Holm p=1.1e-10 | +58.0 % tokens, result +0.113 (40 cells), Holm p=5.6e-11 | -0.4 % tokens, result +0.000 (40 cells), Holm p=5.4e-01 | +75.2 % tokens, result +0.037 (40 cells), p=1.6e-20 | -139.2 % tokens, result -0.113 (40 cells), p=1.0e+00 |
| ai_agents | selfcons | +68.8 % tokens, result +0.150 (40 cells), Holm p=6.6e-27 | +68.8 % tokens, result +0.150 (40 cells), Holm p=4.4e-27 | +47.5 % tokens, result -0.019 (40 cells), Holm p=9.3e-26 | +56.8 % tokens, result +0.081 (40 cells), p=4.5e-16 | -68.5 % tokens, result -0.169 (40 cells), p=1.0e+00 |
| ai_ai | std | +28.3 % tokens, result +0.150 (40 cells), Holm p=4.6e-04 | +28.3 % tokens, result +0.150 (40 cells), Holm p=4.6e-04 | +25.2 % tokens, result +0.175 (40 cells), Holm p=6.7e-03 | – | -4.4 % tokens, result +0.025 (40 cells), p=7.9e-01 |
| ai_human | std | +41.6 % tokens, result +0.218 (38 cells), Holm p=6.1e-21 | +41.6 % tokens, result +0.218 (38 cells), Holm p=3.6e-21 | +0.8 % tokens, result +0.092 (38 cells), Holm p=6.8e-03 | – | -69.8 % tokens, result -0.126 (38 cells), p=1.0e+00 |
| economics | std | +1.42 % (12/12), Holm p=1.7e-09 | – | – | +0.00 % (5/12), p=5.0e-01 | – |
| space | std | +1.67 % (12/12), Holm p=2.8e-09 | – | +1.45 % (12/12), Holm p=1.4e-04 | +1.33 % (12/12), p=1.7e-03 | – |

## Lineage: every move chosen -> RSOS operator

| Row / arm / move | Uses | Kind | Operator |
|---|---|---|---|
| ai_agents|generated|G:route | 552 | lever | route |
| ai_agents|generated|G:zoom | 6 | lever | zoom |
| ai_agents|generated|focus-b0 | 12 | native | beam |
| ai_agents|generated|focus-b1 | 1 | native | beam |
| ai_agents|generated|open | 30 | native | explore |
| ai_agents|generated|restart-b0 | 12 | native | heal |
| ai_agents|generated|stop | 72 | native | no mapping |
| ai_agents|seed3v1|F:blind-b0 | 288 | lever | compress |
| ai_agents|seed3v1|F:blind-b1 | 109 | lever | compress |
| ai_agents|seed3v1|F:blind-b2 | 4 | lever | compress |
| ai_agents|seed3v1|F:reuse-b0 | 27 | lever | inherit |
| ai_agents|seed3v1|F:reuse-b1 | 4 | lever | inherit |
| ai_agents|seed3v1|P4P5-cges | 5 | lever | fuse |
| ai_agents|seed3v1|focus-b0 | 6 | native | beam |
| ai_agents|seed3v1|open | 5 | native | explore |
| ai_agents|seed3v1|stop | 126 | native | no mapping |
| ai_ai|generated|G:beam | 7 | lever | beam |
| ai_ai|generated|G:compress | 1 | lever | compress |
| ai_ai|generated|G:contain | 13 | lever | contain |
| ai_ai|generated|G:fuse | 5 | lever | fuse |
| ai_ai|generated|G:heal | 1 | lever | heal |
| ai_ai|generated|G:pierce | 4 | lever | pierce |
| ai_ai|generated|G:route | 12 | lever | route |
| ai_ai|generated|G:zoom | 8 | lever | zoom |
| ai_ai|generated|chain | 2 | native | fuse |
| ai_ai|generated|focus_home | 6 | native | beam |
| ai_ai|generated|focus_manager | 1 | native | beam |
| ai_ai|generated|focus_mentor | 1 | native | beam |
| ai_ai|generated|focus_office | 3 | native | beam |
| ai_ai|generated|focus_team | 1 | native | beam |
| ai_ai|seed3v1|F:holo-path | 3 | lever | compress |
| ai_ai|seed3v1|F:holo-vote | 38 | lever | compress |
| ai_ai|seed3v1|F:holokey | 16 | lever | compress |
| ai_ai|seed3v1|P3-repair | 4 | lever | heal |
| ai_ai|seed3v1|P4P5-joint | 7 | lever | fuse |
| ai_human|generated|G:heal | 1 | lever | heal |
| ai_human|generated|G:overlay | 1 | lever | overlay |
| ai_human|generated|G:re-host | 1 | lever | re-host |
| ai_human|generated|top | 187 | native | fuse |
| ai_human|generated|unit-0 | 81 | native | beam |
| ai_human|generated|unit-0c | 1 | native | beam |
| ai_human|generated|unit-1 | 23 | native | beam |
| ai_human|generated|unit-1c | 2 | native | beam |
| ai_human|generated|unit-2 | 2 | native | beam |
| ai_human|generated|unit-2c | 1 | native | beam |
| ai_human|seed3v1|F:holo-top | 33 | lever | compress |
| ai_human|seed3v1|F:holomin-top | 212 | lever | compress |
| ai_human|seed3v1|top | 20 | native | fuse |
| ai_human|seed3v1|unit-0 | 33 | native | beam |
| ai_human|seed3v1|unit-0c | 1 | native | beam |
| ai_human|seed3v1|unit-1c | 1 | native | beam |
| ai_human|seed3v1|unit-2 | 1 | native | beam |
| economics|seed3v1|F:otrace:lp_corrected | 18 | lever | heal |
| economics|seed3v1|F:pool:capital_newsvendor | 13 | lever | fuse |
| economics|seed3v1|P4P5:stochastic_lp | 276 | lever | fuse |
| economics|seed3v1|focus_big | 1 | native | beam |
| space|generated|G:beam | 12 | lever | beam |
| space|generated|G:carry | 12 | lever | carry |
| space|generated|G:compress | 219 | lever | compress |
| space|generated|G:fuse | 2 | lever | fuse |
| space|generated|G:heal | 1 | lever | heal |
| space|generated|G:pierce | 4 | lever | pierce |
| space|generated|G:zoom | 9 | lever | zoom |
| space|generated|focus_bulk | 10 | native | beam |
| space|generated|focus_science | 13 | native | beam |
| space|seed3v1|F:holo-carry | 152 | lever | carry |
| space|seed3v1|F:holo-plan | 89 | lever | carry |
| space|seed3v1|P1:counter-shift | 1 | lever | heal |
| space|seed3v1|P3:repair-partial | 1 | lever | heal |
| space|seed3v1|P4P5:exact-planner | 17 | lever | fuse |
| space|seed3v1|focus_science | 14 | native | beam |
