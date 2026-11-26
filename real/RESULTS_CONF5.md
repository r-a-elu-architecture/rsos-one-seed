# RESULTS CONF5 (sealed; analyze_conf5.py exactly as PREREG_CONF5.md)

**LEVEL: STRONG** (2 of 3 rows: the identified RSOS structure beats plain rollout at Holm p < 1e-5, guard and Law 0 held).

| Row | RSOS structure | Cells | vs plain rollout | Holm p | Wins | Guard | Law 0 | Pass |
|---|---|---|---|---|---|---|---|---|
| ai_agents | full | 48 | +43.39 % tokens saved (result +0.120) | 1.9e-13 | 44/48 | ok | ok (2 harmed) | YES |
| ai_ai | v1 | 100 | +3.81 % tokens saved (result +0.140) | 2.5e-01 | 68/100 | ok | ok (7 harmed) | no |
| space | v1 | 20 | +0.74 % result (result +3.718) | 1.5e-08 | 20/20 | ok | ok (0 harmed) | YES |

Means per arm (result, resource):

- ai_agents: default 0.8177, 25.14; rollout 0.8333, 12.93; full 0.9531, 7.318
- ai_ai: default 0.51, 2459; rollout 0.59, 2236; v1 0.73, 2151
- space: default 494.7, 1.505e+04; rollout 499.8, 1.615e+04; v1 503.5, 1.703e+04

AI agents, tokens saved vs rollout by position of the cell in its job (trace persists): 0: +4.71, 1: +6.63, 2: +5.66, 3: +5.43
