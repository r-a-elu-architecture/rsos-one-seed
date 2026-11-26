# PREREG CONF3: an independent, higher-powered confirmation, with the composed arm (25 Nov 2026, ~15:25, UTC+02:00). Layer 1. Confirmatory.

Owner instructions 15:03 and 15:06/15:11. Everything CONF3 runs (this file, the levels, the cell lists, the unit, the
analysis, the workflow, the composed moves exactly as written, the frozen orbit file, the seed, hosts and data) is
committed, fingerprinted (`real/SEAL_CONF3.txt`) and pushed BEFORE any CONF3 cell runs. Nothing is generated or changed
after the seal; later notes are dated addenda that change no rule. Seal commit and push time: `HANDOFF_STRATEGIC.md`.
CONF1, CONF2 (and CONF1 FIX1) are unchanged and finish as sealed; their levels stand on their own.

## Disclosed before the run: why CONF3 exists
CONF3 was designed AFTER the interim CONF1 and CONF2 results were seen (AI agents and AI–human passed; AI–AI missed
1e-5 at 40 cells with d ≈ 0.57; the one-move-per-operator generated arm passed in no row). Its cell numbers were chosen
from those measured effect sizes (power below). A reader should therefore read CONF1, CONF2 and CONF3 together; all are
reported with their levels, and none replaces another. CONF3 uses only fresh cells and its own analysis
(`real/analyze_conf3.py` reads CONF3 outputs only).

## Arms (`cloud/conf3_unit.py`)
standard (`default`), full seed (`seed3v1`), strongest (inventory: scenario stochastic LP; satellite: look-ahead MILP;
AI agents: CGES-style early stopping; AI–human and AI–AI: the standard is the strongest), and **composed**: seed3v1 on a
host whose own levers are replaced by `real/composed/<row>_moves.py`. Leak fix and one fresh process per cell as before.

## The composed arm (correction of a design drift, owner 15:06)
CONF1/CONF2 asked for ONE move per operator; the RSOS grammar is composition (the sequence of operators is the program;
CLAUDE.md §1; map/STRUCTURAL_MAP_22NOV.md; map/QUARK_VAKOG_STRUCTURE.md). A fresh agent that never saw `real/hosts/`,
`real/generated/` or any result received ONLY CLAUDE.md §1, §1a; map/STRUCTURAL_MAP_22NOV.md Parts 0, H, I, J, K;
map/QUARK_VAKOG_STRUCTURE.md; research/sealed/seed/SEED_V3.md; real/HOST_INTERFACE_REAL3v2.md, plus a short domain
description, and wrote at most 5 moves per domain as COMPOSITIONS of operators in VAKOG order (see → choose → act → trace
→ result), with landing per part and the perspectives (above, below, inside, across time). Sealed exactly as written.
The moves see a filtered view (`VIEW` in the unit): AI agents = branch fields only (no task answers); AI–human = the
conversation up to the current turn; AI–AI = A's own facts, what B sent, A's unsent facts; satellite = passes and items
on board. A move that raises on a state is not offered (counted).

## Rows, cells, where
| Row | Model | Cells | Arms | Runs on |
|---|---|---|---|---|
| AI agents (ReAct, self-consistency) | gpt-oss-20b | 701–740 (40), 4 per job | standard, full, strongest, composed | GitHub |
| AI–human | Mistral Small 3.2 | **401–440** (40), 4 per job | standard, full, composed | GitHub |
| AI–AI | gpt-oss-20b + Llama 3.1 8B | 701–850 (150), 5 per job | standard, full, composed | GitHub |
| Inventory | – | 701–712 (12), 1 per job | standard, full, strongest | GitHub |
| Satellite | frozen orbit file | 701–712 (12): standard, full, strongest, composed; 713–724 (12): standard, strongest, composed | | GitHub, 1 per job |
AI–human uses 401–440 because Topical-Chat `test_freq` has 539 conversations (cells index them); 401–440 were never used
(development 1–8, REAL1 101–120, REAL3 201–216, STRUCT1 301–308, CONF1 501–538). Satellite orbit offsets repeat every 6
cells (`cell % 6`), with different on-board data per cell.

## Claims and levels (owner's, fixed now, unchangeable after the run)
One-sided paired t on all cells of a unit; Holm step-down within each claim's family. AI rows: tokens saved with the result
guard (claim 1, claim 3) or a mean result gain ≥ 0 (claim 2).
1. **Cross-domain seed** (full vs standard; AI agents, AI–human, AI–AI, inventory, satellite): **UNPRECEDENTED** = Holm
   p < 1e-5 in all 5 rows; **STRONG** = 3–4; **NOT SHOWN** = fewer.
2. **Communication principle** (AI agents, AI–human, AI–AI): fewer tokens at equal or better result, Holm p < 1e-7 in all
   3 → **UNPRECEDENTED**; 2 → **STRONG**; fewer → **NOT SHOWN**.
3. **The RSOS language composes winning moves** (composed vs standard; AI agents, AI–human, AI–AI, satellite):
   **UNPRECEDENTED** = Holm p < 1e-5 in ≥ 3 of 4 rows; **STRONG** = 2; **NOT SHOWN** = fewer.
What a level measures: the certainty of each comparison at the fixed threshold and the operator lineage of the moves (the
lineage table is reported); it does not by itself establish novelty against prior art.

## Power (from the measured CONF1/CONF2/STRUCT1/REAL3 effect sizes, before the run)
| Row | Measured d | Cells | Expected raw p | Bound after Holm (×6) |
|---|---|---|---|---|
| AI agents ReAct / self-consistency | 1.41 / 4.41 | 40 | 3e-11 / 1e-27 | 2e-10 / 7e-27 |
| AI–human | 3.24 | 40 | 9e-23 | 5e-22 |
| AI–AI (tokens) | 0.57 | 150 | 5e-11 | 3e-10 |
| Inventory | 2.62 | 12 | 1e-6 | 6e-6 (reachable, little margin) |
| Satellite | 2.55 | 12 | 1e-6 | 7e-6 (reachable, little margin) |
Composed arm: no prior measurement; for reference the CONF2 one-move generated arm gave d ≈ 1.8 in satellite (→ ~1e-8 at
24 cells) and d ≈ 0.5 in AI–AI tokens (→ ~4e-9 at 150 cells) if composed moves are at least as strong.

## Budget (checked before the run)
GitHub Actions on this repository ≈ 9,990 job-minutes this month including running jobs (≈ $56 of the $90 cap at 3,000
included minutes, ≈ $64 at 2,000). CONF3 ≈ 12 satellite full-seed jobs × ~60 min + 12 composed-only × ~8 + 12 inventory ×
~8 + 50 AI jobs × ~4 ≈ 1,100 minutes ≈ $9: total ≈ $65–73, within $90. All 24 satellite cells fit. OpenRouter: the
workflow stops AI jobs if less than $1 is left.
