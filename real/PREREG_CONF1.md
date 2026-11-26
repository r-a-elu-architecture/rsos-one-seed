# PREREG CONF1: confirmatory test of the full sealed seed at a very small error threshold (25 Nov 2026, ~14:45, UTC+02:00). Layer 1. Confirmatory.

Owner's instruction 14:11 and 14:25 (budget answer). Written, hashed and pushed BEFORE any CONF1 run, in two seals:
**seal A** (`real/SEAL_CONF1_A.txt`: this file, the unit, the analysis, the workflows) before the satellite and inventory
runs; **seal B** (`real/SEAL_CONF1_B.txt`: the generated moves, exactly as written, plus seal A) before the AI-row run.
No CONF1 result is read between the two seals. Both seals are disclosed.

## Question
REAL3 and STRUCT1 showed the full seed (`real/seed3.py`, mode `seed3v1`, unchanged) beating the standard in AI agents,
AI–human, inventory and satellite, and STRUCT1 showed the gain comes from host-written levers, each mapped to an RSOS
operator by the host's `op_of` table. CONF1 asks: with many fresh cells and a very small error threshold, is the full
seed's gain over the standard established beyond reasonable doubt in all four domains, and does every lever it uses trace
to an RSOS operator? Secondary: does a fresh agent, given only the RSOS language sources, write moves that do the same?

## Arms (cloud/conf1_unit.py; all existing modes)
`default` (standard), `seed3v1` (full seed), `strongest` (inventory: scenario stochastic LP; satellite: look-ahead MILP;
AI agents: CGES-style early stopping; AI–human: none, the standard is the strongest), and in the AI rows `generated`:
seed3v1 on a host whose `primitives()`/`frame()` are replaced by `real/generated/<row>_moves.py`. Leak fix as STRUCT1
(stores and trace cleared before every arm, one fresh process per cell); REAL3 FIX1 calc wrapper applied.

## The generated arm (seal B)
A fresh agent that has not seen the hosts receives only: `map/STRUCTURAL_MAP_22NOV.md` (Parts 0, H, I, J, K),
`map/QUARK_VAKOG_STRUCTURE.md`, `research/sealed/seed/SEED_V3.md`, `real/HOST_INTERFACE_REAL3v2.md`, `CLAUDE.md` §1 and
§1a, plus a short domain description per AI row (what the state holds and the native actions; no host lever, no
standard-method code, no results). It writes one move per RSOS operator as a Python function `state -> native action or
None`. The moves are sealed exactly as written; a move that raises on a state is simply not offered (counted).

## Rows, cells, where each runs
| Row | Model | Cells | Runs on |
|---|---|---|---|
| AI agents (standards ReAct and self-consistency = 2 units) | gpt-oss-20b | 501–540 (40) | GitHub, 4 cells per job |
| AI–human | Mistral Small 3.2 | 501–540 (40) | GitHub, 4 cells per job |
| Inventory | – | 501–512 (12) | **this Claude workspace** (2 cores), free; same unit, same seal |
| Satellite downlink | real orbits (CelesTrak elements fetched by each job) | 501–512 (12) | GitHub, 1 cell per job |
All cells are fresh (never used before). Satellite orbit offsets repeat every 6 cells (`cell % 6`): 12 cells cover 6
geometries twice, with different on-board data. Disclosed.

## Decision (fixed now; real/analyze_conf1.py)
- Primary family, Holm step-down adjusted p over the 5 units, full seed vs standard, one-sided paired t on all cells.
  Inventory, satellite: result gain. AI rows: tokens saved, with the result guard (mean result gain ≥ 0, or its 95 %
  lower bound ≥ −2 % of the standard's mean).
- A domain passes if one of its units has Holm-adjusted **p < 1e-5** (AI rows **p < 1e-7**) and the guard holds.
- Operator trace: every host-written lever (names starting `P` or `F:`) the full seed chose maps to an RSOS operator via
  the host class's own `op_of()` or the seed's `COMMON` table, both written before this test. Native branches are
  reported with their mapping where one exists; disclosed before the run: AI agents' native `stop` (commit early) has
  no mapping in those tables and is not part of the criterion.
- **Levels (owner's, fixed now, unchangeable after the run):**
  - **UNPRECEDENTED:** the full seed beats the standard in all 4 domains at those thresholds AND every lever traces to
    an RSOS operator.
  - **STRONG:** 2–3 domains.
  - **NOT SHOWN:** fewer.
  What the top level measures: the statistical certainty of the gain over each domain's standard and the operator
  lineage of every lever used. It does not by itself establish novelty against prior art (paper §7).
- Secondary (separate Holm family, same thresholds, reported): generated vs standard in the AI rows. It decides whether
  the operator language alone produced moves that beat the standard. Also reported: full seed vs strongest, generated vs
  full seed.

## Budget and reachable level (stated before the run)
GitHub Actions on this repository: ≈ 9,600 billed minutes this month (≈ $53 of $60 assuming 3,000 included minutes;
the biology FIX2 run was cancelled at the owner's instruction, biology stays UNDECIDED on 6 of 8 cells). CONF1 needs
≈ 720 minutes for satellite (12 single-cell jobs, ~57 min per cell) and ≈ 130 for the AI rows: ≈ $7. Inventory runs here.
Reachable p-level from the measured effect sizes (REAL3 and STRUCT1, d = 2.4–2.7): at 12 cells, raw one-sided p ≈
1e-6 to 2.4e-6 for satellite and 8e-7 to 2e-6 for inventory, about 2e-6 to 5e-6 after Holm: the 1e-5 threshold is
reachable at the measured effect, with little margin. If the GitHub budget stops some satellite jobs, the analysis uses
the cells that finished, and the count is reported. OpenRouter: $1.01 of $20 used; the workflow stops the AI rows if less
than $1 is left.
