# PILOT2 notes (26 Nov 2026; development cells 1-16 only; screening, never confirmation)

AI-AI, real models (gpt-oss-20b as A, llama-3.1-8b as B), cloud run 45752250769, 12 jobs, no crash.
Arms: plain rollout; v1 (RSOS shapes A only, the CONF5 arm); whole (v1 + B shaped by the same structure: Eagle
skeleton and hologram of the whole; + the system sees itself: an answer counts only when the agent's own view holds the
whole chain). Code: real/pilot/pilot2_whole.py; outputs: real/pilot/out2/.

| Arm | Accuracy | Tokens |
|---|---|---|
| plain rollout | 0.812 | 1546 |
| v1 | 0.938 | 1585 |
| whole | 1.000 | 1080 |

whole vs rollout: accuracy better in 3 cells, worse in 0; tokens lower in 14 of 16 (-466 per cell, dz 0.61).
Development cells are easier than fresh cells (CONF5 fresh cells: plain rollout 0.59), so the confirmation uses 200 cells.
