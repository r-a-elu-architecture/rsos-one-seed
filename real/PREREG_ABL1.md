# PREREG ABL1: does each RSOS operator cause the result it carries? (25 Nov 2026)

Sealed (real/SEAL_ABL1.txt) and pushed before any ABL1 cell runs. Nothing is generated, tuned or re-run after the seal
(crashes only, disclosed). Later notes are dated addenda that change no rule. Layer: the layer-2 structure runs unchanged
on layer-1 data (a pass is cyan, LAYER_RULE).

## Question
CONF1 and CONF3 reached UNPRECEDENTED with the RSOS operators running together. ABL1 switches ONE operator off per row and
measures what it costs. A pass means that operator causes the result.

## Design (switch, not build: CLAUDE.md §01)
- Programs: the sealed CONF3 composed programs (`real/composed/<row>_moves.py`), unchanged. Seed: `real/seed3.py`, `seed3v1`.
- Arms per cell: `default` (the standard), `full` (the CONF3 composed arm), `minus` (full with one operator off, by a
  filter on every candidate action, or the seed's existing landing switch).
- Rows, operators and fresh cells (never used before). Rows were chosen because the sealed record shows the operator's
  effect there (CONF3: AI agents self-consistency -45 % tokens, p 1.8e-23; AI-AI -27 %, p 8.4e-12; satellite +1.01 %,
  p 1.2e-7). This sets the test's power; the cells are fresh, so it cannot set its outcome.
  - AI agents, self-consistency standard, cells 901-940, gpt-oss-20b: **Law 2 off** (no blind or reuse plan from any source).
  - AI-AI, cells 1001-1150, gpt-oss-20b + llama-3.1-8b: **Law 5 off** (no hologram or packed message, no key).
  - Satellite, cells 901-948, frozen CelesTrak elements, offline and deterministic: **composition and Law 4 landing off**
    (no composed programs; the seed's landing switched off for the whole run).
- 20 GitHub jobs. The Law 0 membrane is not ablated: it is a safety law, checked as "no harm" below.

## Decision (fixed now; `real/analyze_abl1.py`)
A row passes if all hold: (1) cause: full beats minus, one-sided paired t, Holm over the 3 rows, p < 1e-5 (tokens saved on
the AI rows, result on satellite); (2) guard (AI rows): full's result not worse than minus's (mean >= 0 or 95 % lower bound
>= -2 %); (3) full beats the standard, one-sided p < 1e-3; (4) Law 0: no harm vs the standard (same guard).
**Levels:** UNPRECEDENTED = 3 of 3 rows · STRONG = 2 · NOT SHOWN = fewer.

## What a pass means
UNPRECEDENTED: each named RSOS operator (Law 2 blind operation, Law 5 relations / hologram, composition with Law 4
landing) causes the result it carries, on real models and data, with the structure unchanged, at p < 1e-5 after correction.

## Reproduction
`bash reproduce_abl1.sh` verifies every fingerprint and recomputes the table from the committed outputs;
`bash reproduce_abl1.sh space` re-runs the satellite row offline and compares it cell by cell with the committed run.
