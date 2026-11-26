# T2b results (layer 2), private

Predictions: `PREREG_T2B.md` (sha256 `cae47165…e005`, commit 77a154c, before any code). Code: `t2b.py` (commit
6a4b3cb, before any result). Data: `RESULTS_T2B.json`. 32 scenes × 300 facts; budget 10,000 bits per scene for every
arm (0.222 of compact JSON). Run 20 Nov 2026, 02:2x–02:5x Vilnius. Code unchanged during the run.

## Strongest finding

**The living hologram holds under repeated damage.** Five rounds of fresh 30 % damage: the plain hologram (T2r)
falls to 67.9 %. The living one (heal + reading through relations + strength/selection + roads) reads **99.75 %**
after round 5, and its wrong write-backs stay at **0.5–1.2 %** per round. Healing alone (R2) reaches 92.9 % with
6.8–11.1 % wrong write-backs: the combination cuts wrong write-backs about tenfold. The combination is the result.

## Single damage: exact accuracy

| Arm | 0 % | 10 % | 30 % | 50 % | 70 % | 90 % |
|---|---|---|---|---|---|---|
| T2r (plain) | 99.50 | 99.07 | 97.73 | 93.17 | 81.92 | 52.74 |
| A rooms | 99.35 | 98.83 | 96.84 | 92.41 | 79.96 | 51.19 |
| B line codes | 79.43 | 78.23 | 74.90 | 70.83 | 63.53 | 44.82 |
| D explain-away, 2 passes | **100** | **100** | **100** | **99.79** | 94.68 | **57.06** |
| F grey, 2 bits × 5,000 | 97.45 | 96.35 | 92.79 | 85.85 | 72.02 | 45.47 |
| R34 road codes | 89.31 | 87.92 | 85.26 | 80.33 | 69.90 | 47.82 |
| R5 explain-away to stable | **100** | **100** | **100** | **99.97** | **97.39** | 55.58 |
| R6 strength + selection | 100 | 99.99 | 99.71 | 96.65 | 84.92 | 52.04 |
| Static (A+B+D) | 80.44 | 79.53 | 76.22 | 71.52 | 62.81 | 43.59 |
| **Living** (R2+R34+R5+R6) | 99.96 | 99.97 | 99.89 | **99.50** | 73.90 | 33.64 |
| JSON, same share destroyed | 100 | 29.44 | 14.89 | 14.90 | 14.98 | 15.12 |
| Chance | 14.78 | | | | | |

Height at 50 %: T2r 82.1 → D 99.2, R5 99.9, Living 97.4, R6 94.4; B 19.0, R34 36.6.
Mean error for x, y, height at 50 % (value steps): T2r 1.13; B 2.06; R34 1.73; D 0.064; R5 0.007; Living 0.009.

## Repeated damage: 5 rounds of fresh 30 %

| Arm | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| T2r | 97.63 | 93.14 | 86.25 | 76.53 | 67.89 |
| R2 heal only | 97.63 | 96.12 | 94.87 | 93.70 | 92.87 |
| R5 | 100 | 99.95 | 98.80 | 92.43 | 78.17 |
| Static | 76.38 | 71.10 | 65.54 | 58.84 | 52.87 |
| **Living** | **99.94** | **99.87** | **99.83** | **99.78** | **99.75** |

Wrong write-backs: R2 6.8 / 8.5 / 9.6 / 10.6 / 11.1 %; Living 0.53 / 0.92 / 0.93 / 1.10 / 1.18 %.

## Predictions

| # | Result | Measured |
|---|---|---|
| P1 reproduction | **pass** | identical to stored T2 |
| P2 rooms within ±1.5 pp | **fail** | rooms slightly worse; −1.96 pp at 70 %, −1.55 at 90 % |
| P3 line codes halve the error | **fail** | error 1.82× larger (2.06 vs 1.13); exact lower, as predicted |
| P4 road codes halve the error | **fail** | error 1.53× larger (1.73 vs 1.13) |
| P5 D beats T2r ≤ 70 %, ≥ 96 % at 50 % | **pass** | 99.79 % |
| P6 R5 ≥ D everywhere | **fail** | at 90 %: 55.58 vs 57.06 (passes at all other levels) |
| P7 R6 beats T2r ≤ 70 %, ≥ 96 % at 50 % | **pass** | 96.65 % |
| P8 grey does not beat T2r at 50 % | **pass** | 85.85 vs 93.17 |
| P9 Static ≥ 96 %, height ≥ 90 % | **fail** | 71.52 %, height 19.4 % |
| P10 Living ≥ 97 % and height ≥ 90 % at 50 %; ≥ 90 % at 70 % | **fail** (as one row) | 50 % clauses pass (99.50, height 97.38); 70 % stretch fails (73.90) |
| P11 Living ≥ 2 × JSON at 50 % | **pass** | 6.7× (99.50 vs 14.90) |
| P12 repeated damage | **pass** | Living 99.75 %; T2r 67.89 %; wrong write-backs ≤ 1.18 % |
| P13 Living beats Static | **pass** | 99.50 vs 71.52; 99.75 vs 52.87 |

**7 pass, 6 fail.**

## Diagnosis (written after the results)

1. **Reading through relations (rule 5) is the strongest single lever.** T2's weakness was not storage but the
   reading: the same stored bits read 93.2 % plainly and 99.97 % through the relations of the other facts.
2. **The ordered codes as built were a mistranslation of rules 3–4.** Standard level vectors make neighbours almost
   identical (adjacent heights 98 % alike), which destroys the unique fingerprint the owner specified. Order was
   kept, uniqueness lost: exact accuracy and error size both got worse. Rule 3 says *unique* fingerprint; the next
   build must keep order **and** near-uniqueness.
3. **This is why Living collapses at 70–90 %** (73.9 %, 33.6 %) while R5 alone holds 97.4 % at 70 %: the road codes
   are the weak component, and at heavy damage the reweighting estimated from wrong reads amplifies the error.
4. **Rooms at fixed budget change nothing useful** (as predicted in direction, slightly worse in size).
5. **Grey at equal budget loses** (predicted). The owner's rule 6, strength kept by the writer within the same
   budget, wins instead: 100 % at 0 %, 96.65 % at 50 %.
6. **JSON collapses at the first damage** (29 % at 10 % loss, chance from 30 %); the hologram still reads 52–57 % at
   90 % loss.

## Next test (not run; needs its own sealed predictions)

T2c: Living without roads (R2+R5+R6), and roads rebuilt with order plus near-unique fingerprints, against R5 at
70–90 % and in repeated damage up to 10 rounds.
