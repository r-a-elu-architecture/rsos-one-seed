# REASON1 (draft, not sealed): does an RSOS operator pass improve reasoning beyond a second look?

Status: draft, 20 Nov 2026. To be sealed and run after today (layer 2: models as reasoners and judges). Seeds:
`PILOT_REASONING_20NOV.md` (two pilots, order confound noted).

## Question
After a first plain answer to a hard practical problem, does a pass with RSOS operators add more new, distinct,
usable ideas than (a) a second plain pass or (b) a pass with a generic creativity checklist?

## Design
- **Problems:** 24, written before sealing, in four kinds (constraint, scheduling, design, diagnosis), six each;
  half from the project's own history (labelled), half new and outside it.
- **Reasoners:** 3 model families (as in A9). Each problem: one plain pass P1, then three second passes from the same
  P1, in random order, in separate calls:
  - **Again:** "Think once more; add what is missing."
  - **SCAMPER:** substitute, combine, adapt, modify, put to other use, eliminate, reverse.
  - **RSOS:** the operator card (host decides, route by state, re-host, zoom, mirror, inherit, sequence is the
    program, contain, heal, fuse, pierce), each with one line of meaning, no examples from the problem's domain.
  Prompts are matched for length (± 10 % tokens).
- **Outcome:** ideas added beyond P1, extracted by a fixed prompt, deduplicated, then rated blind by 3 judge models
  from families other than the reasoner (and, if available, 2 people) as *new*, *distinct* and *usable* (each 0/1).
  Primary: count of ideas rated all three by ≥ 2 of 3 judges.
- **Analysis:** per problem × reasoner, RSOS − Again and RSOS − SCAMPER; Wilcoxon signed-rank, one-sided; Holm for two
  comparisons. Secondary: judges' preference ranking of the three passes; idea categories.

## Predictions (to finalise before sealing)
- R1: RSOS > Again on the primary outcome (p < 0.05 after Holm).
- R2: RSOS > SCAMPER on the primary outcome (p < 0.05 after Holm).
- R3: the advantage holds on the new problems, not only on the project's own.
- What counts against RSOS, in advance: if RSOS ≈ SCAMPER, the operators act as a generic checklist; if RSOS ≈ Again,
  the pilots' gain was the second look.

## Open before sealing
Problem list; judge prompt; exact operator card text; blinding check (judges guess the arm at chance).
