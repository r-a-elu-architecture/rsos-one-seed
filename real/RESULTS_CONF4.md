# RESULTS CONF4 (sealed; analyze_conf4.py exactly as PREREG_CONF4.md)

**LEVEL: NOT SHOWN** (1 of 4 rows: the RSOS language's programs beat the control programs at Holm p < 1e-5, with no harm, used >= 25 %, above the floor).

| Row | Standard | Cells | RSOS vs control | Holm p | Wins | Guard | Law 0 | RSOS use | Control use | RSOS vs std | Control vs std | Structure vs std | Pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ai_agents | react | 40 | +43.9 % tokens (result +0.019) | 4.9e-16 | 39/40 | ok | ok (6 harmed) | 87 % | 90 % | +4.34 | -0.939 | -0.922 | YES |
| ai_agents | selfcons | 40 | +10.1 % tokens (result -0.006) | 2.0e-02 | 24/40 | FAIL | ok (9 harmed) | 72 % | 90 % | +16.4 | +15.2 | +12.3 | no |
| ai_ai | std | 150 | +1.5 % tokens (result -0.040) | 6.0e-01 | 76/150 | FAIL | ok (18 harmed) | 71 % | 76 % | +931 | +895 | +833 | no |
| ai_human | std | 40 | -0.3 % tokens (result +0.005) | 1.0e+00 | 16/40 | ok | ok (9 harmed) | 18 % | 19 % | +0.126 | +0.13 | +0.00982 | no |
| space | std | 24 | -0.0 % result (result -0.196) | 1.0e+00 | 6/24 | ok | ok (0 harmed) | 97 % | 97 % | +14.3 | +14.5 | +7.43 | no |

Rows: ai_agents: PASS, ai_human: no, ai_ai: no, space: no

## Each agent vs the control mean (secondary)

| Row | Standard | R1 | R2 | R3 | C1 | C2 | C3 |
|---|---|---|---|---|---|---|---|
| ai_agents | react | +3.67 (use 87 %) | +5.68 (use 91 %) | +6.5 (use 83 %) | -2.15 (use 89 %) | -0.928 (use 93 %) | +3.07 (use 87 %) |
| ai_agents | selfcons | +2.94 (use 87 %) | +0.421 (use 77 %) | +0.107 (use 52 %) | -0.419 (use 91 %) | -0.692 (use 92 %) | +1.11 (use 87 %) |
| ai_ai | std | +28.5 (use 71 %) | +31.8 (use 70 %) | +46.2 (use 73 %) | +36.2 (use 70 %) | +8.87 (use 78 %) | -45.1 (use 80 %) |
| ai_human | std | +0.0196 (use 20 %) | -0.0243 (use 17 %) | -0.0063 (use 16 %) | -0.0407 (use 13 %) | +0.0289 (use 23 %) | +0.0118 (use 22 %) |
| space | std | -0.159 (use 97 %) | -0.251 (use 97 %) | -0.177 (use 97 %) | +0.12 (use 97 %) | -0.055 (use 97 %) | -0.0647 (use 97 %) |
