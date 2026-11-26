# Rename: White Dragon "balls" → "spheres" (owner, 17 Nov 2026, 11:22–11:23)

A sphere is a graph node with spatial extent: a surface, an interior and a core. Landings have a position and a
depth, and spheres can nest. Owner's terms: ball (09:20), sphere (11:22).

Renamed in code: `src/rsoslang/data/metric_balls.json` → `metric_spheres.json`; `dragon.py`, `tests/test_dragon.py`,
`experiments/{e1_dragon,f1_feedback,f1b_feedback,f1_diag}.py`; register rows U101–U103. Pre-registrations and
reports written before the rename keep the word "ball" (they are frozen records).

Not renamed: the statement `BALL` (U7, chat 1 T70: one trigger → one coloured ball), a different operator.

Check (rerun after the rename): F1 and F1b `results_sha256` identical (93f4c710…, daf7caf1…). E1: all 276
numeric fields identical; its hash changed from 6e0909a3… to 66445733… only because the hash also covers field
names (`lacking_balls` → `lacking_spheres`). 82 tests pass.
