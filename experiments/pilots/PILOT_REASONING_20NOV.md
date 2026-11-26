# Pilot: plain reasoning vs an RSOS operator pass (exploratory, 20 Nov 2026)

Status: **pilot, not evidence.** Recorded before any formal test. Reasoner: Claude (Opus 5.5) in the build session.
Known confound: the RSOS pass always came **second**; a second look of any kind may add ideas. n = 2, not blind.
Purpose: seed for REASON1 (to be pre-registered after the 20 Nov launch).

## P1 (08:41 Vilnius): the laptop cannot run the arms that see a 300-key state

- Plain pass: run the open model elsewhere (Colab free T4; Kaggle; Groq/OpenRouter free tiers too capped for
  tool-calling); or shrink the tasks (weaker). Answer: re-host to Colab.
- RSOS pass (host decides; route by state / select partial modules; re-host; zoom; mirror; fuse):
  re-host as above, **plus** (1) zoom: run 30 / 100 / 300 keys and seal the error-window law's curve per arm before the
  run; (2) mirror: the weak host becomes a measurement (prompt size and wall time per arm show cost ∝ requests for
  blind vs ∝ state for JSON Patch).
- New, usable ideas added by the RSOS pass: 2 (zoom curve; constraint → measurement).

## P2 (08:46 Vilnius): fit three sizes × four arms × several families before 15:00 without cutting scope

- Plain pass (as stated afterwards): run in parallel; cut cells.
- RSOS pass: inherit (reuse sealed A7/A8 300-key cells as labelled anchors; predictions only on new cells);
  in unison (parallel hosts); sequence is the program (decisive cells first, each cell its own verdict);
  contain (budget cap per host; sandbox for model-written Python); heal (auto-resume); fuse (one runner, scorer ready
  before data); pierce (tasks from a drand round after the seal).
- New, usable ideas beyond the plain pass: 2 (inherit; decisive-first ordering). Caps, resume and parallelism are
  ordinary engineering.

## Candidate operator compositions (build status: practised, twice, by the assistant)

- **mirror(constraint) → measurement**
- **inherit + sequence**: keep full scope with fewer calls; strongest result first

## REASON1 design implied by the pilots

Three arms on the same problem: plain → plain again; plain → generic checklist (SCAMPER); plain → RSOS operators.
Outcome: count of new, distinct, usable ideas, judged blind. 20–30 problems, several reasoner models, blind judges.
RSOS counts only if it beats both controls.
