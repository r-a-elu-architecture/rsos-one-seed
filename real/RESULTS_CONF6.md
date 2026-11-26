# RESULTS CONF6 (sealed; analyze_conf6.py exactly as PREREG_CONF6.md)

**LEVEL: UNPRECEDENTED** (AI-AI, 200 fresh cells: whole-system RSOS vs plain rollout on accuracy and tokens, Holm over 2, Law 0).

| Contrast | Accuracy gain | Better / worse cells | Holm p (acc) | Tokens saved | Lower-token cells | Holm p (tokens) |
|---|---|---|---|---|---|---|
| **whole vs plain rollout** | +0.125 | 25 / 0 | 1.3e-07 | +51.4 % | 180/200 | 5.1e-28 |

Law 0 (no harm vs the standard): held.

Means per arm (accuracy, tokens):

- default: 0.795, 3129
- rollout: 0.875, 2645
- v1: 0.925, 2420
- whole: 1.000, 1286
- noholo: 0.995, 1287

Secondary (decides nothing; unadjusted one-sided p):

| Contrast | Accuracy gain (p) | Tokens saved (p) |
|---|---|---|
| whole_vs_v1 | +0.075 (4.2e-05) | +46.9 % (1.2e-29) |
| whole_vs_noholo | +0.005 (1.6e-01) | +0.1 % (4.8e-01) |
| whole_vs_default | +0.205 (7.5e-12) | +58.9 % (6.7e-39) |
| v1_vs_rollout | +0.050 (3.4e-02) | +8.5 % (2.3e-03) |
