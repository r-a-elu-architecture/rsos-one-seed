# T5 pre-registration: the same dot in different hosts, on real data (written before running)

A re-implementation of chat 2's EXP-014 and EXP-016 (chat 2 T38, T41–T46), whose code was not captured.

**Hosts:** three real datasets bundled with scikit-learn:
- breast cancer (569 samples);
- wine (178);
- handwritten digits (1,797).

**Learner:** an online linear classifier (`SGDClassifier`, log loss), trained over 300 steps of 16 samples:
- steps 1–100: before injection;
- steps 101–200: the dots fade in;
- steps 201–300: fully integrated.

Held-out split: 30%, stratified, fixed per seed.

**Dots:** each is written in the RSOS Language as `DOT <dot> INTO learner.training` and compiled; the compiled
program decides the learner's options.

| Dot | Source domain (chat 2) | What it does in the learner |
|---|---|---|
| bio | Memory (hippocampal replay) | Half of each batch replays examples the learner got wrong earlier, at the same batch budget |
| chem | Catalysis | Raises the learning rate for features that co-vary strongly with the current errors |
| music | Rhythm | A periodic learning-rate pattern: strong beat, weak beats, period 8 steps |
| feedback | Control | Lowers the learning rate when the running error rises, raises it when it falls |

**Design:** 16 configurations (none, each dot alone, all pairs, triples, all four) × 3 hosts × 6 seeds = 288 runs.
The effect is the change in final held-out accuracy against no dots, paired by seed.

| # | Hypothesis (from chat 2) | Pass rule |
|---|---|---|
| H1 | The same dot behaves differently in different hosts (chat 2: bio −2.160 pp wine, +0.586 pp digits) | For the bio dot alone, at least one host with mean effect > 0 and at least one with mean effect < 0, and at least one 95% bootstrap CI excluding 0 |
| H2 | The host decides which combination is best (chat 2 EXP-016: Spearman −0.28 to −0.22; top-combination overlap 0) | The best of the 15 dot configurations differs between at least two hosts, and the mean pairwise Spearman correlation of the 15 effects across hosts is below 0.5 |
| H3 | Combining is not additive (n+1) | In at least one host, the best combination's effect differs from the sum of its dots' single effects by more than the larger CI half-width of the singles |
