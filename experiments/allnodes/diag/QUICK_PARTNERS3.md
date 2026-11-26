# PARTNERS3 pair test (road 10, fixes 1+2, common randomness) (23 Nov 2026 ~14:05, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Dev seeds 6520, 6521; 20 bridge pairs x 2 = 40 cells. Code `partners3.py` (0db89e2, before the run). Numbers
`QUICK_PARTNERS3.json`, `partners3_p*.json`.

## Result: FAILS (1 of 5) — tubes do not beat no tubes on pairs → by K.5, n = 4 and n = 8 leave the seal
| Check | Result | Pass |
|---|---|---|
| Q1 joined > best organism alone | 39/40 | yes |
| Q2 joined > notubes | **25/40**; mean gain +0.0011 (10th–90th pct −0.003 … +0.0065; 13 cells lower) | **no** |
| Q3 worst channels not worse than notubes | 19/40 | **no** |
| Q4 each organism ≥ itself alone (K.4 b) | 22/40 (A 31, B 29) | **no** |
| Q5 no landed action above a world's bound | 67 ticks (joined 6, notubes 61 — notubes guards only its own world by design) | **no** |
Mean pair G: joined 0.9693 · notubes 0.9682 · aloneA 0.9512 · aloneB 0.9511 · native 0.9302.
Joined events: 4,800 proposals; 213 refused in phase 2 (80 fell back to phase 1, 133 to default); 401 P4 changes.

## Reading
Against PARTNERS1 the fixes moved the gain over no tubes from −0.0008 to +0.0011 and Q2 from 20 to 25 of 40: a real
but small effect, inside cell-to-cell spread. In this host each organism already reads its partner through the
coupling of its own world; knowing the partner's move for one tick adds about 0.1 point. A second organism is worth
~2 points (Q1 39/40); the tube between them is not yet worth anything measurable. Q5's 6 joined ticks come from the
default fallback, which is landed without its own projection check.

Erratum (23 Nov 14:11): the time in the title was an estimate and is late by about 1-2 h; the exact time is the git commit time.
