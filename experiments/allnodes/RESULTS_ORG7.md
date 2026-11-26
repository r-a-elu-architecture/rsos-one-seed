# ORG7 results: organism v2 with counter-shift — all 21 shades green (sealed e41836c; analyze_org7.py; ANALYSIS_OUT_ORG7.txt)

Run on the owner's laptop, 22–23 Nov 2026 ~19:35–02:30 Kyiv, 4 parts in parallel, fresh seeds 9490–9501 (12), worlds
9960. Data commit d66b178. The analysis was re-run here from the pushed eval files and gives the same per-shade lines
(the laptop's text file differs only in encoding, UTF-16 from PowerShell).

## Sealed predictions
| ID | Prediction | Result | Verdict |
|---|---|---|---|
| R1 | channels pass in ≥ 19/21 | **21/21** (12/12 in every shade) | **PASS** |
| R2 | ≥ 15/21 green | **21/21** | **PASS** |
| R3 | all 21 green | **21/21** | **PASS** |
| R4 | control, transfer, worlds pass | control 139/156 (p 3e-25); transfer 105/150 (p 5e-7); WB 19/21, WC 19/21 (p 1e-4 each) | **PASS** |

Every shade: beats the native 12/12; beats the strongest baseline (strongest native or beam-only) 12/12 (v21: 11/12;
Holm p 0.005 for all); channels 12/12; repeat [6, 6] (v21 [5, 6]).

## Check after the run (descriptive, not sealed)
Counter-shift alone (the native methods plus the new rule, no organism roles) on the same 252 runs: the organism beat
it in **247**, lost 4. Counter-shift alone also cleared the bar in 6 shades (v5 11/12, v9, v10, v14, v18, v19 12/12):
there the new rule carries part of the green; everywhere the organism adds beyond it.

## Roadmap (map/ROADMAP_LAYER2_23NOV_0245.html)
New green rows (turquoise): Information theory · Mathematics: operator algebra · Distributed systems · Protocol theory ·
Databases · Ledgers, finance · Mathematics · Human reasoning · Linguistics · Earth and space · Level B · Level C (L2;
real data on par, L1 evidence only). **Totals 29 → 41 green (all turquoise), 21 → 9 yellow, 1 grey.**
Still yellow: All laws as mathematics; Meaning (the house: not tested); Level D (births failed); Level E (living-host
part not built); roads 2, 3 (launch), 8 (physical layer, first beam). Grey: road 10 (partners).

## Method note
The owner's method (22 Nov 16:05): diagnose structurally (DIAG1), build from the structural map (Part I), quick loops on
development seeds (counter-shift 41/42), seal, one confirmatory run. ORG7 is the first sealed run built this way and
the first to fill all 21 shades.

## Erratum (23 Nov 2026 ~06:15, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius) — open until re-checked
Found by the laws row (LAWS2, experiments/laws/diag/QUICK_LAWS2.md) and confirmed independently here: org7.py's
counter-shift (`ps = [i] + ps[:-1]`) ADDS a landing when that side has no pick, so a tick can use 5 landings instead
of the shared budget of 4. Measured on arm v2 (the ORG7 organism): 17/2,520 ticks (LAWS1 seeds), 50/2,520 ticks (LAWS2
seeds); natives, beam-only and own6: 0. Independent check on 3 shades (dev seed 7400): 1/180 ticks.
Consequence: ORG7's 21/21 was measured with an organism that occasionally (about 0.7–2 % of ticks) used one extra
landing. The sealed numbers stay as recorded; the 12 rows that turned green under ORG7 are **pending re-check** with a
budget-correct counter-shift in the next combined sealed run. If they do not repeat, they return to started.
Responsibility: the defect is in org7.py as written in the previous session.
