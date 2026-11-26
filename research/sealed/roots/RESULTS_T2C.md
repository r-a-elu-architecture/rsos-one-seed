# T2c results (layer 2), private

Predictions: `PREREG_T2C.md` (sha256 `7b2a6295…7c4a12`, commit 622e354, before any code). Code: `t2c.py`
(commit 9de440e; the codecs were checked on synthetic data only before the run). Data: `RAW_T2C_part0/1.json`,
`RESULTS_T2C.json`. 16 scenes; load test 8 sets per size. Budget 10,000 bits for every arm. Run 20 Nov 2026,
~03:25–03:45 Vilnius; code unchanged during the run.

## Strongest finding

**Beyond the cliff the hologram wins; inside it, today's method wins.** The classic erasure code reads 100 % up to
85 % destroyed, then falls to chance (15 %) at 90 %. The hologram degrades gradually: **54–57 % at 90 %, 38–39 % at
95 %, 26–27 % at 98 %** destroyed, 3.6×, 2.6× and 1.8× the classic code. Inside the threshold, under repeated
damage with healing, under silent flips and at high load, the classic code is equal or better.

## Known erasures, single (exact %)

| Arm | 0 | 50 | 70 | 85 | 90 | 95 | 98 | 99 |
|---|---|---|---|---|---|---|---|---|
| R5 | 100 | 99.98 | 97.17 | 71.85 | **56.65** | **39.27** | **26.88** | 22.44 |
| LivNR (no gate) | 100 | 99.92 | 99.40 | 50.48 | 37.73 | 28.10 | 22.46 | 19.10 |
| LivNRg | 100 | 99.92 | 96.65 | 70.92 | 54.31 | 38.08 | 26.15 | 20.85 |
| LivRd50g | 100 | 99.77 | 95.79 | 69.75 | 54.25 | 37.48 | 25.04 | 21.29 |
| LivRd25g | 100 | 99.85 | 96.77 | 71.17 | 55.02 | 37.54 | 26.02 | 22.38 |
| **Classic-E** | 100 | **100** | **100** | **100** | 14.98 | 14.46 | 14.50 | 15.00 |

Chance 14.8 %. Mean error x, y, height at 70 %: R5 0.59, LivNR 0.013, LivNRg 0.33, LivRd50g 0.28, LivRd25g 0.34.

## Repeated damage, 10 rounds of fresh 30 % (exact % after rounds 1, 5, 10)

| Arm | 1 | 5 | 10 |
|---|---|---|---|
| R5 (no healing) | 100 | 78.40 | 30.54 |
| LivNR / LivNRg | 100 | 99.98 | 99.96 |
| LivRd25g | 100 | 100 | 99.94 |
| LivRd50g | 100 | 91.94 | 47.52 |
| Classic-E (heals) | 100 | 100 | 100 |

Wrong write-backs ≤ 0.93 % per round in every healing hologram arm.

## Silent flips (exact %)

| Arm | 5 % | 10 % | 20 % | 30 % | 40 % |
|---|---|---|---|---|---|
| R5 | 100 | 99.52 | 91.00 | 65.40 | 35.92 |
| LivNRg | 100 | 99.92 | 89.73 | 64.48 | 34.54 |
| LivRd25g | 99.98 | 99.94 | 89.69 | 64.67 | 34.54 |
| Classic-R (repetition) | 99.98 | 99.50 | **93.71** | **69.94** | **36.02** |

## Load at 50 % erasure (exact %)

| Facts | R5 | LivNRg | Classic-E |
|---|---|---|---|
| 600 | 92.98 | 95.04 | 100 |
| 1,200 | 66.07 | 66.00 | 100 |

## Predictions: 6 pass, 3 fail

| # | Result | Measured |
|---|---|---|
| C1 classic 100 % ≤ 85 % | **pass** | 100 at 0, 50, 70, 85 |
| C2 classic cliff ≤ 20 % | **pass** | 14.5–15.0 |
| C3 LivNRg thresholds, above classic beyond the cliff | **pass** | 99.92 / 54.31 / 38.08; above at 90, 95, 98 |
| C4 classic beats every hologram at 70 and 85 % | **pass** | 100 vs ≤ 99.40; 100 vs ≤ 71.85 |
| C5 gate +10 pp at 90 %, neutral ≤ 50 % | **pass** | +16.58 pp; identical at 0 and 50 |
| C6 roads ≥ 99 % at 50 %, error at 70 % ≤ LivNRg | **fail** | Rd50 passes; Rd25 error 0.3358 vs 0.3337 (miss by 0.002) |
| C7 repeated damage | **pass** | LivNRg 99.96, classic 100, R5 30.54 |
| C8 hologram ≥ repetition under flips | **fail** | 89.73 vs 93.71 at 20 %; 64.48 vs 69.94 at 30 %; 34.54 vs 36.02 at 40 % |
| C9 load | **fail** | 600: 95.04 (pass); 1,200: 66.00 (< 70) |

## Diagnosis (after the results)

1. **The gate fires too early.** It held at every erasure level from 50 % up, in all 16 scenes. It rescues 90 %
   (+16.6 pp) but costs 70 % (LivNR 99.40 → LivNRg 96.65). Its threshold (half the facts weak) needs calibration.
2. **The gate and the 50 % roads interact.** With neighbours 50 % alike, plain reads look unsure, the gate holds,
   healing stops, and damage accumulates (47.5 % after 10 rounds). With 25 % roads healing runs and holds 99.94 %.
3. **The owner's corrected roads removed the T2b collapse** (Living with roads at 70 %: T2b 73.90 → T2c 96.77 with
   Rd25), but do not yet beat the road-less structure on exact accuracy.
4. **Healing is not a unique advantage:** a classic code that re-encodes after reading also holds 100 % forever.
   T2b's strongest finding stands against the plain hologram, not against today's method.
5. **Silent flips:** even simple repetition beats the hologram above 10 % flips; a strong code would beat it by
   more. No advantage found there.
6. **Load:** at 1,200 facts in 10,000 bits the hologram is at 66 %; the classic code is still exact.
7. **Prior art on point 1 of the strongest finding:** graceful degradation of distributed and uncoded
   representations beyond a code's threshold is a known property (uncoded / analog transmission, distributed
   vector codes). The measured advantage is real; the property alone is not new.

## Next hypothesis (register; not run)

Combine instead of compete: in one budget, a classic code for exactness inside the threshold plus the hologram as
the structure that still knows beyond it, and as soft information that helps the classic decoder past its cliff.
