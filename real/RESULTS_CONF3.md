# RESULTS CONF3 (sealed; analyze_conf3.py exactly as PREREG_CONF3.md; CONF3 outputs only)

- **Claim 1, cross-domain seed: STRONG** (4 of 5 rows at Holm p < 1e-5)
- **Claim 2, communication principle: UNPRECEDENTED** (3 of 3 rows at Holm p < 1e-7, equal or better result)
- **Claim 3, the RSOS language composes winning moves (composed arm): UNPRECEDENTED** (3 of 4 rows at Holm p < 1e-5)

| Row | Standard | Full seed vs standard (claim 1) | Tokens (claim 2) | Composed vs standard (claim 3) | Full seed vs strongest | Composed vs full seed |
|---|---|---|---|---|---|---|
| ai_agents | react | +48.4 % tokens, result +0.106 (40 cells), Holm p=2.3e-08 | +48.4 % tokens, result +0.106 (40 cells), Holm p=7.7e-09 | -4.1 % tokens, result -0.013 (40 cells), Holm p=7.6e-01 | +68.3 % tokens, result +0.081 (40 cells), p=4.2e-18 | -101.8 % tokens, result -0.119 (40 cells), p=1.0e+00 |
| ai_agents | selfcons | +61.2 % tokens, result +0.131 (40 cells), Holm p=3.6e-21 | +61.2 % tokens, result +0.131 (40 cells), Holm p=2.2e-21 | +45.3 % tokens, result +0.019 (40 cells), Holm p=1.8e-23 | +49.7 % tokens, result +0.106 (40 cells), p=6.5e-12 | -41.0 % tokens, result -0.113 (40 cells), p=1.0e+00 |
| ai_ai | std | +25.0 % tokens, result +0.133 (150 cells), Holm p=2.6e-09 | +25.0 % tokens, result +0.133 (150 cells), Holm p=1.3e-09 | +27.2 % tokens, result +0.133 (150 cells), Holm p=8.4e-12 | – | +3.0 % tokens, result +0.000 (150 cells), p=1.4e-01 |
| ai_human | std | +42.3 % tokens, result +0.175 (40 cells), Holm p=1.2e-24 | +42.3 % tokens, result +0.175 (40 cells), Holm p=8.1e-25 | +0.7 % tokens, result +0.080 (40 cells), Holm p=2.9e-02 | – | -72.1 % tokens, result -0.095 (40 cells), p=1.0e+00 |
| economics | std | +1.34 % (12/12), Holm p=1.4e-05 | – | – | +0.04 % (3/12), p=1.1e-01 | – |
| space | std | +1.98 % (11/11), Holm p=1.4e-06 | – | +1.01 % (22/23), Holm p=1.2e-07 | +0.90 % (11/11), p=2.1e-04 | -0.67 % (0/11), p=1.0e+00 |

## Lineage: every move chosen -> RSOS operator

| Row / arm / move | Uses | Kind | Operator |
|---|---|---|---|
| ai_agents|composed|C:see>trace>beam>step | 46 | lever | see>trace>beam>step |
| ai_agents|composed|focus-b0 | 11 | native | beam |
| ai_agents|composed|focus-b1 | 6 | native | beam |
| ai_agents|composed|open | 51 | native | explore |
| ai_agents|composed|restart-b0 | 15 | native | heal |
| ai_agents|composed|stop | 130 | native | no mapping |
| ai_agents|seed3v1|F:blind-b0 | 287 | lever | compress |
| ai_agents|seed3v1|F:blind-b1 | 108 | lever | compress |
| ai_agents|seed3v1|F:blind-b2 | 2 | lever | compress |
| ai_agents|seed3v1|F:reuse-b0 | 24 | lever | inherit |
| ai_agents|seed3v1|F:reuse-b1 | 1 | lever | inherit |
| ai_agents|seed3v1|P4P5-cges | 4 | lever | fuse |
| ai_agents|seed3v1|focus-b0 | 5 | native | beam |
| ai_agents|seed3v1|focus-b1 | 1 | native | beam |
| ai_agents|seed3v1|open | 11 | native | explore |
| ai_agents|seed3v1|stop | 125 | native | no mapping |
| ai_ai|composed|C:see>trace>choose>contain>act | 22 | lever | see>trace>choose>contain>act |
| ai_ai|composed|C:see>trace>compress>inherit>contain>act | 100 | lever | see>trace>compress>inherit>contain>act |
| ai_ai|composed|C:see>trace>fuse>contain>act | 21 | lever | see>trace>fuse>contain>act |
| ai_ai|composed|C:see>trace>pierce>contain>act | 32 | lever | see>trace>pierce>contain>act |
| ai_ai|composed|chain | 11 | native | fuse |
| ai_ai|composed|focus_city | 2 | native | beam |
| ai_ai|composed|focus_home | 43 | native | beam |
| ai_ai|composed|focus_manager | 2 | native | beam |
| ai_ai|composed|focus_mentor | 1 | native | beam |
| ai_ai|composed|focus_office | 15 | native | beam |
| ai_ai|composed|focus_team | 18 | native | beam |
| ai_ai|seed3v1|F:holo-path | 15 | lever | compress |
| ai_ai|seed3v1|F:holo-std | 5 | lever | compress |
| ai_ai|seed3v1|F:holo-vote | 182 | lever | compress |
| ai_ai|seed3v1|F:holokey | 74 | lever | compress |
| ai_ai|seed3v1|P3-repair | 16 | lever | heal |
| ai_ai|seed3v1|P4P5-joint | 21 | lever | fuse |
| ai_ai|seed3v1|focus_office | 1 | native | beam |
| ai_human|composed|C:see>inside>beam>choose>act | 7 | lever | see>inside>beam>choose>act |
| ai_human|composed|C:see>present>choose>act | 2 | lever | see>present>choose>act |
| ai_human|composed|top | 177 | native | fuse |
| ai_human|composed|unit-0 | 94 | native | beam |
| ai_human|composed|unit-1 | 29 | native | beam |
| ai_human|composed|unit-1c | 4 | native | beam |
| ai_human|composed|unit-2 | 2 | native | beam |
| ai_human|composed|unit-2c | 1 | native | beam |
| ai_human|composed|unit-4c | 1 | native | beam |
| ai_human|seed3v1|F:holo-top | 26 | lever | compress |
| ai_human|seed3v1|F:holomin-top | 242 | lever | compress |
| ai_human|seed3v1|top | 16 | native | fuse |
| ai_human|seed3v1|unit-0 | 31 | native | beam |
| ai_human|seed3v1|unit-0c | 1 | native | beam |
| ai_human|seed3v1|unit-1 | 1 | native | beam |
| ai_human|seed3v1|unit-1c | 1 | native | beam |
| economics|seed3v1|F:otrace:lp_corrected | 18 | lever | heal |
| economics|seed3v1|F:otrace:pool_corrected | 1 | lever | heal |
| economics|seed3v1|F:pool:capital_newsvendor | 10 | lever | fuse |
| economics|seed3v1|P4P5:stochastic_lp | 280 | lever | fuse |
| space|composed|C:see>choose>contain>act | 3 | lever | see>choose>contain>act |
| space|composed|C:see>colour>route>contain>act | 11 | lever | see>colour>route>contain>act |
| space|composed|C:see>future>compress>inherit>contain>act | 483 | lever | see>future>compress>inherit>contain>act |
| space|composed|focus_bulk | 11 | native | beam |
| space|composed|focus_science | 18 | native | beam |
| space|seed3v1|F:holo-carry | 128 | lever | carry |
| space|seed3v1|F:holo-plan | 88 | lever | carry |
| space|seed3v1|P1:counter-shift | 2 | lever | heal |
| space|seed3v1|P4P5:exact-planner | 19 | lever | fuse |
| space|seed3v1|focus_science | 15 | native | beam |
