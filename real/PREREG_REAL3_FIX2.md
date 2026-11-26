# REAL3 FIX2: re-run of the biology pair that timed out (25 Nov 2026, ~12:50, UTC+02:00). Written before the re-run.

The biology re-run of FIX1 (run 45549039454) finished pairs 0, 1 and 3; pair 2 (cells 205-206) was cancelled at the
job limit (345 min) without producing a result. This is a timeout, not a code error. Owner decision 12:41: re-run only
pair 2, disclosed, with enough time; then decide biology on all 8 stage-1 cells with the sealed rule
(`real/analyze_real3.py`, unchanged); if it is still UNDECIDED it is reported as undecided, with no stage 2 (budget).
How: `cloud/real3_unit_fix2.py` is the FIX1 unit with two differences only: it reads `real/SEAL_REAL3_FIX2.txt` (the
FIX1 hash list plus this note and the FIX2 unit and workflow), and an optional env `REAL3_CELL` runs one cell of the
pair. Cells 205 and 206 each run in their own job (360 min, GitHub's maximum), so each cell has a whole machine. Seed,
host, data, modes and analysis are exactly as sealed. Disclosed in the results and the paper.
