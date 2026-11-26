# RESULTS ABL1 (sealed; analyze_abl1.py exactly as PREREG_ABL1.md)

**LEVEL: NOT SHOWN** (0 of 3 rows: switching the row's RSOS operator off costs the result at Holm p < 1e-5; full RSOS beats the standard; no harm).

| Row | Operator switched off | Cells | Full vs minus | Holm p | Wins | Guard | Full vs standard (p) | Law 0 | Pass |
|---|---|---|---|---|---|---|---|---|---|
| ai_agents | Law 2 (blind plan) off | 40 | -0.3 % tokens saved (result +0.037) | 1.0e+00 | 20/40 | ok | +11.5 (1.1e-25) | ok (8 harmed) | no |
| ai_ai | Law 5 (hologram / key) off | 150 | +1.3 % tokens saved (result +0.007) | 5.1e-01 | 66/150 | ok | +841 (3.3e-16) | ok (2 harmed) | no |
| space | composition + Law 4 landing off | 48 | -0.1 % result (result -0.627) | 1.0e+00 | 20/48 | ok | +5.84 (1.5e-15) | ok (1 harmed) | no |

Means per arm (result, resource):

- ai_agents: default 0.7812, 26.03; full 0.8125, 14.52; minus 0.775, 14.48
- ai_ai: default 0.9067, 3006; full 0.98, 2165; minus 0.9733, 2194
- space: default 510, 1.521e+04; full 515.9, 1.627e+04; minus 516.5, 1.662e+04
