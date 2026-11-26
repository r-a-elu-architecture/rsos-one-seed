# REAL3 FIX1: re-run of the units that crashed in stage 1 (25 Nov 2026 ~07:00, UTC+02:00). Written before the re-run.

Stage 1 run 45536337290 (seal ed5a2f5) crashed in 5 of 48 units on code errors, before producing any result:
1. biology, all 4 pairs (cells 201-208): `ModuleNotFoundError: sec1_real` when the host is imported inside a spawned
   worker process (the sealed ORG-REAL1 code adds a relative path, "../sec1", that the worker does not resolve).
   Fix: no code change; the re-run sets `PYTHONPATH=<repo>/experiments/sec1`.
2. AI agents, Llama 3.1 8B, pair 3 (cells 207-208): a model-written `calc` expression that does not parse raised
   `SyntaxError` inside the blind runtime and stopped the job. Fix: the FIX1 unit wraps the blind runtime's `calc` so that a
   `SyntaxError` becomes a plan error (the same path as every other invalid plan: re-plan, then fallback). No sealed
   file is edited; behaviour is unchanged wherever the sealed code did not crash.
Everything else is exactly as sealed (PREREG_REAL3.md, analyze_real3.py, cells, modes, rules). The re-run uses
`cloud/real3_unit_fix1.py`, a copy of the sealed unit that differs only in reading `real/SEAL_REAL3_FIX1.txt` (the
sealed hash list plus this note and the FIX1 unit) and in the `calc` wrapper. These 5 units are re-run; results of the
other 43 units are untouched. Stage 2 (if any) also runs through the FIX1 unit and workflow, so the same two crashes
cannot recur there. Disclosed in the results and the paper.
