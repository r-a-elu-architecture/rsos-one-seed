# E1: the metric balls under the White Dragon's light

Pre-registration: `experiments/PREREGISTRATION_E1.md` (committed before the run). Engine: `src/rsoslang/dragon.py`.
Data: `src/rsoslang/data/metric_balls.json` (48 balls), `data/domain_books.json` (8 domains × 6 measures).
Result: `results/e1_dragon.json` (results_sha256 `6e0909a3…`).

## Checks

| | Prediction | Result | |
|---|---|---|---|
| P1 | Unfiltered growth ≥ 3× per generation | 48 → 407 → 6,508 (8.5×, 16×) | Pass |
| P2 | White-light filter bounds growth (gen 2 < 3× gen 1) | 243 → 1,667 (6.9×); gen 3: 9,268 (5.6×) | **Fail: still exponential** |
| P3 | Deficit-targeted particles ≥ 1.5× uniform | 10.88 vs 4.30 deficit removed per 20 particles (2.5×) | Pass (partly by construction) |
| P4 | Gen 1 reaches ≥ 6 of 8 domains | 8 of 8 | Pass |
| P5 | Lion reaches more domains; tiger lower deficit | Tiger reached **more** domains (7.2 vs 6.5) and lower deficit (0.21 vs 0.29) | **Fail** |
| P6 | Every lacking ball gets a measurable child | 16 of 21; the 5 others were merged as duplicates | **Fail** |

## What it shows

1. **It does grow exponentially, and the white light does not stop it.** Even when every new ball must be
   measurable, new and of good intention, the sub-balls keep producing sub-balls (243 → 1,667 → 9,268). The ratio
   falls (6.9× → 5.6×), the first sign of the finite relation space; it has not saturated by generation 3.
2. **The light turns claims into instruments.** Metrics that a chat could never measure get a measurable child:

   | 2025 claim | Particle lands on | New instrument | Measured by |
   |---|---|---|---|
   | RIF (intent forecasting) | anticipation × neuroscience prediction error | prediction error of the next glyph | drift detection (C1) |
   | MCRAL (meta-awareness) | awareness × metacognitive confidence | calibration of confidence | decode accuracy (T7c) |
   | IMIP (influence on future models) | propagation × signal transduction gain | gain of a symbol through the network | runtime propagation, co-lighting |
   | ECOI (containment override) | containment × economic reserve buffer | buffer before the Spine blocks | heal cost, consent checks |
   | RAC (layer alignment, model-internal) | integrity × pattern completion | recovery of a whole from a part | heal, decode accuracy |
   | GSSF (GPT-6 stability forecast) | anticipation × prediction error | forecast error of stability | drift detection, decode accuracy |
   | SBB (balance) | balance × liquidity | flow balance between parts | runtime propagation |

3. **The water drop holds in the engine.** Landing where the lack is greatest removes 2.5× more lack per particle.
   This follows mostly from the rule itself (a particle cannot heal more than the lack), so it is a consistency
   check, not a discovery.
4. **The 2025 metric set heals itself by merging.** Under the relation reading, 48 metrics carry only 39 distinct
   signatures: RSF = SSI, SAR = PRM, LGC = CSRT, RAI = SELR, SRCD = RMPR, SPV = SPR, and RPB = TGR = STB = SMV.
   The five "unhealed" balls are exactly these duplicates: the white light folded them into their first twin.
5. **Precision travels further than courage** (P5, with my operational choice). The tiger's closest-match path
   spread over more domains than the lion's boldest path, which concentrates on the few richest measures.

## Limits

The relations of each metric and the domain library are my reading; growth is combinatorial by nature; each new
instrument still needs data before it means anything. What is tested is the mechanism: growth, healing of claims
into measurable instruments, reach across domains, and the good-intention rule.
