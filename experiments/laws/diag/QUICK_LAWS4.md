# LAWS4 (last development round for row 1): result by cause (24 Nov 2026, commit time exact; UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Dev seeds 6430, 6431. Collect on the laptop (17e364f), scope recorded before reading (eb88d1b): collect-based checks on
shades 1–8 x 2 seeds = 16 cells (shades 9–12 also arrived and are excluded by that scope); LE, L5, L3 on all 21
shades (local part, 1590fe1). One execution fix: the summary lines now use the recorded scope (they still looped over
21 shades and stopped with a KeyError). Numbers `QUICK_LAWS4.json`.

## Result: FAILS (8 of 13) — owner's rule: stop and report by cause
| Check | Result | Pass | Cause |
|---|---|---|---|
| EXACT | 6/6 | yes | — |
| L0 constitution (membrane, protect last) | **16/16** | yes | — |
| L1′ / L1 / L2 | 159/161 · 214/214 · 211/214 | yes | — |
| C2 common point / C1 consistency | 208/214 · 0 conflicts in 20 pairs | yes | — |
| PR violations predict the result | **16/16 cells, ρ −0.85** | yes | — |
| L4 landing (owner's K.2 definition) | 9/16; made precision median 0.913 | **no** | **measurement noise**: the need forks met different world events (LAWNEED: this measure agrees 60 % with the noise-free reference) |
| RC cost of responses | cost 14/16 (two cells −0.020, −0.023), margin 16/16 | **no** | withholding/re-targeting driven by the noisy need (1,048 withheld, 235 re-targeted, 146 refused, 195 gated) |
| LE error events (fresh replay of the same element) | 74/102 (dry 24/26, drift 50/76) | **no** | **law domain**: 21 of 31 failing spans are T = 8; measured below predicted (median −0.074): several onsets per span, where the linear form (T ≪ τ) over-counts; τ/2 is not ≪ τ |
| L5 relations (reading a partly lost state) | 10/21; |ΔCE| ≤ 0.003 bit | **no** | **host**: under the organism the relations carry ~no information about a unit's drift state |
| L3 living structure | 35/42 (keep 41, gradual 41, keeps more than native 35) | **no** | the organism's loss under damage equals the native's within 0.001–0.013 in 7 shade x seed |
