# PREREG CONF2: three claims, decided together with CONF1 (25 Nov 2026, ~15:15, UTC+02:00). Layer 1. Confirmatory.

Owner instructions 14:20, 14:23 and 14:28. Everything CONF2 runs is committed, fingerprinted (`real/SEAL_CONF2.txt`) and
pushed BEFORE any CONF2 cell runs: this file, the claim levels, the cell lists, the unit, the analysis, the workflow, the
generated moves exactly as written, and the frozen orbit file. Nothing is generated or changed after the seal; any later
note is a dated addendum that changes no rule. The seal commit and push time are recorded in `HANDOFF_STRATEGIC.md`.
CONF1 (`real/PREREG_CONF1.md`, seals A and B, addendum FIX1) is unchanged and keeps its own level; CONF2 adds rows and
decides three claims over the CONF1 and CONF2 outputs together (`real/analyze_conf2.py`).

## What CONF2 runs (`cloud/conf2_unit.py`, a copy of the CONF1 unit; `.github/workflows/rsos_conf2.yml`)
| Row | Model | Cells | Arms | Where |
|---|---|---|---|---|
| AI–AI | gpt-oss-20b (A) with Llama 3.1 8B (B) | 601–640 (40), 4 per job | standard, full seed (seed3v1), generated (the standard is the strongest) | GitHub |
| Satellite downlink | real orbits, frozen file | 601–612 (12), 1 per job | standard, strongest (look-ahead MILP), generated | GitHub |
Satellite's full seed is measured in CONF1 (cells 501–512); CONF2 adds its generated arm on new cells. Energy and robotics
are not run: at affordable sizes they cannot reach p < 1e-5 (measured effect sizes d = 0.77 and 1.43 give p ≈ 1e-2 and
2e-4 at 12 cells); they are reported at their REAL3 levels.

## The generated arm
A fresh agent that never saw `real/hosts/` received only the RSOS language sources (`map/STRUCTURAL_MAP_22NOV.md` Parts
0, H, I, J, K; `map/QUARK_VAKOG_STRUCTURE.md`; `research/sealed/seed/SEED_V3.md`; `real/HOST_INTERFACE_REAL3v2.md`;
`CLAUDE.md` §1, §1a) and a short description of each domain, and wrote one move per RSOS operator:
`real/generated/ai_ai_moves.py`, `real/generated/space_moves.py` (AI agents and AI–human: CONF1 seal B). The moves are
sealed exactly as written. They replace the host's own levers (primitives and frame; native branches stay) and see a
filtered view of the state (`VIEW` in the unit): AI–AI = A's own facts, what B sent, A's unsent facts, never B's
values; satellite = the pass schedule and the items on board, no random generators.

## Claims and levels (owner's, fixed now, unchangeable after the run)
All tests one-sided paired t over all cells of a unit; Holm step-down within each claim's family. AI rows: tokens saved
with the result guard (mean result gain ≥ 0, or its 95 % lower bound ≥ −2 % of the standard's mean).
1. **Cross-domain seed** (full seed vs standard; AI agents [ReAct, self-consistency], AI–human, AI–AI, inventory,
   satellite). **UNPRECEDENTED** = Holm p < 1e-5 in **all 5 rows**; **STRONG** = 3–4 rows; **NOT SHOWN** = fewer.
2. **Communication principle** (meaning through structure, not volume; AI agents, AI–human, AI–AI): fewer tokens at
   equal or better result (mean result gain ≥ 0). **UNPRECEDENTED** = Holm p < 1e-7 in **all 3 rows**; **STRONG** = 2;
   **NOT SHOWN** = fewer.
3. **Operator language** (generated vs standard; AI agents, AI–human, AI–AI, satellite). **UNPRECEDENTED** = Holm
   p < 1e-5 in **at least 3 of 4 rows**; **STRONG** = 2; **NOT SHOWN** = fewer.
Every move chosen by the full seed and by the generated arm is listed with its RSOS operator (host `op_of`, the seed's
`COMMON` table, or the generated move's own operator name) in the lineage table of `RESULTS_CONF2.md` and paper §5.5.
What a level measures: the statistical certainty of each comparison at the fixed thresholds and the operator lineage of
the moves; it does not by itself establish novelty against prior art.

## Data and budget (stated before the run)
Frozen orbit file: see `real/PREREG_CONF1_FIX1.md`; fingerprinted here. Topical-Chat is not used in CONF2. AI–AI cells are
generated from the cell number (no external data). GitHub Actions budget raised to $90 by the owner: ≈ $60 committed
before CONF2 (incl. CONF1 and its FIX1); CONF2 ≈ 12 satellite jobs × ~60 min + 10 AI–AI jobs × ~3 min ≈ $6. OpenRouter:
the workflow stops AI jobs if less than $1 is left. Reachable levels at the measured effect sizes: AI–AI d ≈ 1.07 →
p ≈ 2e-8 at 40 cells (claim 1 reachable; claim 2's 1e-7 reachable with little margin); satellite generated arm unknown
(new moves).
