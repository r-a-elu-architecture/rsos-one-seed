# BEAM1 quick test: road 8, the first beam (23 Nov 2026 ~07:50, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)

Development seeds: worlds 6440, 6441; channels 6450+. Budget B = 29 frames of 16 bytes per tick, fixed before the run
on throwaway seed 6499 (1.25 x the delta native's median 23 frames; beam median 2; snapshot 39–40). Code `beam1.py`
(pushed before the run, 18b4e67). Numbers: `QUICK_BEAM1.json`, `beam1_p0.json`, `beam1_p1.json`.
21 shades x 2 seeds x 3 carriers x 3 loss levels = 378 lossy runs, + 42 zero-loss runs.

## Result: 3 of 4 criteria pass; criterion 4 fails as coded, by a build defect in the zero-loss run

| Criterion | Result | Pass |
|---|---|---|
| (1) no wrong adoption (beam) | 0 wrong; READY caught 497 undetected frame corruptions (snap 489, delta 494) | yes |
| (2) beam > best native in every carrier x loss cell | 9/9 | yes |
| (3) beam ≥ best native per run, ≥ 90 % | 378/378 | yes |
| (4) K exact: lossless replay equals the sender at every tick | replay exact in **42/42 runs (every tick)**; but the coded check also required zero-loss sync = 1.0 and got 0.983 | **no (as coded)** |

Mean sync (share of ticks at which the receiver holds the sender's exact current state):

| Carrier | m = 0.1 beam / delta | m = 0.3 | m = 0.5 |
|---|---|---|---|
| light | 0.974 / 0.721 | 0.977 / 0.284 | 0.946 / 0.068 |
| radio | 0.968 / 0.754 | 0.977 / 0.282 | 0.978 / 0.036 |
| matter | 0.973 / 0.866 | 0.984 / 0.203 | 0.987 / 0.020 |

Snapshot native: 0.000 everywhere (39–40 frames never fit the budget of 29 in one tick).

## Reading
- **Mechanism:** the receiver holds the world's laws, so only what the laws cannot know crosses the carrier: the action
  and the world's own events of the tick (median 2 frames against 23 for the strong native). Law 5 on the carrier:
  the relations known to the reader move the limit. The channel coding (MDS parity, frame check, READY) is identical
  for all arms; the margin is the structure, not the coding.
- **Criterion 4:** the zero-loss run still applied the 1e-3 per-frame undetected-corruption model, so READY refused
  exactly one message per run (42 caught in 42 runs) and that tick was out of sync (59/60 = 0.983, the same for delta).
  The replay itself is exact. The check is not changed; the defect is in the build of the zero-loss run (zero loss
  should mean no corruption too). A fix belongs in the next version, before any seal.
- **Disclosed simplifications:** ideal MDS erasure code (decode iff k frames arrive), lossless 1-bit feedback,
  undetected corruption modelled as a flag that READY catches (not real bit flips), initial sync of the static world
  excluded for all arms.
