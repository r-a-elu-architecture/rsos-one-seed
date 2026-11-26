# PAINT-1 pre-registration: gestures on a painted agent workflow (written before running)

**Program:** the 12-module support-ticket workflow (`src/rsoslang/agents/`).
**Benchmark sets** (fixed before running):
- development: seed 1, 200 tickets, clean;
- held-out A: seed 2, 500 tickets, 30% typos, 30% unseen phrasing;
- held-out B: seed 3, 500 tickets, same mix.

Results are measured on A and B only.

**Gestures** are written in the RSOS Language and compiled to program changes (`src/rsoslang/painting/scene.py`):
- PIERCE … THROUGH node.head | node.heart | node.brain;
- PLACE … NEAR node;
- DOT;
- SHIFT node TO grey;
- HEAL;
- MOVE.

**What this tests.** That every gesture has an exact, distinct and measurable meaning in a real program, and that the
place decides the result (R14). It does **not** test whether editing the painting is better than editing code: that
is the proof run (step 7). The guest modules were written by the assistant, so their benefits are expected by
design. The test is that the painting's operators deliver them exactly, at the right place and only there.

| # | Hypothesis | Pass rule |
|---|---|---|
| H1 | The place decides: the spell corrector and the synonym expander, each placed at classify's head, heart, brain and near, give at least 3 distinct (accuracy, cost) outcomes each | ≥ 3 distinct on A |
| H2 | Near acts on the neighbours, not on the node: the spell corrector near classify leaves classify's errors unchanged | classify errors equal to baseline on A |
| H3 | Grey on act contains the crashes without lowering accuracy | crashed = 0 and accuracy ≥ baseline, on A and B |
| H4 | The cache lowers cost only where it has meaning: in the heart of memory (and in its brain), not at its head | cost(heart) < cost(base) ≤ cost(head) on A |
| H5 | A composed program (corrector + expander in the brain of classify, cache in the heart of memory, fast retry in the heart of act, act grey) scores higher than the baseline | score higher on A and B |
