# PREREG CONF4: does the RSOS language itself make better decision programs? (25 Nov 2026)

Written and sealed (real/SEAL_CONF4.txt) before any CONF4 cell runs. The programs are sealed exactly as the agents wrote
them. Nothing is regenerated, tuned or re-run after the seal; crashes only, disclosed. Later notes are dated addenda
that change no rule.

## Question
CONF1–CONF3 showed that generated and composed moves beat the standard. They did not show that the **RSOS language**
causes the gain: the same AI without the language was never tested. CONF4 tests this directly.

## Design (switch, not build: CLAUDE.md §01)
- **Six fresh agents, same model, same domain text** (`real/conf4/DOMAINS.md`, identical action interfaces, including the
  `blind`, `holo` and key channels for everyone).
  - **R1, R2, R3 (RSOS):** also receive the full language: CLAUDE.md §1/§1a, LAYER_RULE.md, map/STRUCTURAL_MAP_22NOV.md,
    the VAKOG maps (V1, V2 corrections, quark), OPERATOR_GAP, RSOS_APPLIED_UNIVERSAL, SEED_V1–V3, MATH_V1,
    spec/LANGUAGE.md, HOST_INTERFACE_REAL3v2, the operator register U1–U171 (public and private), the symbol and
    specification records. They write programs as houses: rooms by state, VAKOG chains in the host's order, laws in
    law form (invariant + scope + check + response), Laws 0–6, library P1–P9.
  - **C1, C2, C3 (control):** receive only DOMAINS.md and are told to use their full expertise.
  - At most 5 programs per domain each; standard library only; functions of the filtered state only.
- **Engine:** every arm runs inside the same sealed seed (`real/seed3.py`, mode `seed3v1`: shared selector, own-future
  valuation over forks, membrane, Law 4 landing, observer). The programs replace the host's levers. Arms per cell:
  `default` (the standard), `structure` (no programs: the floor), R1–R3, C1–C3.
- **Rows and fresh cells (never used before):** AI agents 40 cells (801–840, gpt-oss-20b; units react and self-consistency),
  AI–human 40 (Topical-Chat test_freq 441–480, mistral-small-3.2), AI–AI 150 (801–950, gpt-oss-20b + llama-3.1-8b),
  satellite 24 (801–824, frozen CelesTrak elements; fully offline and deterministic). 51 GitHub jobs.

## Decision (fixed now; `real/analyze_conf4.py`)
Per cell: RSOS = mean of R1–R3; CONTROL = mean of C1–C3. Deciding quantity: tokens saved (AI rows, free resource) or
result gain (satellite, fixed budget). One-sided paired t per unit; Holm over the 5 units.
A unit passes if all hold: (1) Holm p < 1e-5; (2) result guard vs control (mean ≥ 0 or 95 % lower bound ≥ −2 % of the
control's mean); (3) **Law 0**: no harm vs the standard (same guard); (4) **Law 4**: the RSOS programs are the chosen
action in ≥ 25 % of decisions; (5) **floor**: RSOS adds over the structure arm. A row passes if any unit passes.

**Levels:** UNPRECEDENTED = ≥ 3 of 4 rows pass · STRONG = 2 rows · NOT SHOWN = fewer.

## What a result means
- UNPRECEDENTED: the language itself, given to an AI, produces programs that beat the same AI's best expert programs,
  across unrelated hosts, without harm, at p < 1e-5 after correction. This is the causal claim CONF1–3 could not make.
- NOT SHOWN: the gains of CONF1–3 come from the engine and the channels, not from the language as text. Reported as is.
- Limits stated now: three agents per side (agent variance enters through the per-cell mean, not as a random effect);
  one model family writes all programs; the satellite row is deterministic, the AI rows are not.

## Reproduction
`bash reproduce_conf4.sh` verifies every fingerprint and recomputes the table from the committed outputs;
`bash reproduce_conf4.sh space` re-runs the satellite row offline and compares it cell by cell with the committed run.
