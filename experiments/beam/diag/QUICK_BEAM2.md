# BEAM2 quick test: road 8, beam vs deterministic lockstep (23 Nov 2026 ~08:25, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)

Development seeds: worlds 6460, 6461; channels 6470+. B = 29 frames per tick. Code `beam2.py` (pushed before the run,
ebc2f57; smoke test on throwaway 6499 only). Numbers: `QUICK_BEAM2.json`, `beam2_p0.json`, `beam2_p1.json`.
378 lossy runs + 42 zero-loss runs; lossy feedback (one acknowledgement frame per tick, same carrier process).

## Result: 4 of 5 criteria pass; beam > lockstep in 8 of 9 cells (one exact tie) → ROW FAILS the quick test

| Criterion | Result | Pass |
|---|---|---|
| (1) no wrong adoption (beam) | 0; READY caught 312 (lockstep 313, snap 360, delta 340) | yes |
| (2a) beam > lockstep in every cell | **8/9** (matter 0.1: 0.8508 = 0.8508, tie) | **no** |
| (2b) beam > max(snap, delta) in every cell | 9/9 | yes |
| (3) beam ≥ every native per run, ≥ 90 % | 378/378 (beam > lockstep in 68 runs, < in 0) | yes |
| (4) zero loss: replay exact, sync = 1.0 | beam 42/42 exact, sync 1.0 in 42/42 (lockstep exact 42/42) | yes |

Mean sync at B = 29 (beam / lockstep / delta):

| Carrier | m = 0.1 | m = 0.3 | m = 0.5 |
|---|---|---|---|
| light | 0.863 / 0.862 / 0.658 | 0.690 / 0.687 / 0.240 | 0.461 / 0.440 / 0.043 |
| radio | 0.846 / 0.844 / 0.675 | 0.699 / 0.695 / 0.226 | 0.493 / 0.478 / 0.017 |
| matter | 0.851 / 0.851 / 0.766 | 0.667 / 0.666 / 0.167 | 0.488 / 0.485 / 0.009 |

## What the beam adds beyond lockstep (descriptive, no criterion)
- **Message size:** median 2 frames (beam) vs 3 (lockstep) vs 23 (delta) vs 39 (snapshot). The beam's own addition is
  the structure coding: visits coded with the shared popularity (Law 5) and onsets listed only for eligible units.
  Everything else in BEAM1's margin over delta comes from **lockstep itself** (both ends hold the simulation).
- **Where it matters — tight budgets (mean sync, beam / lockstep):**

| B (frames/tick) | light 0.1 | light 0.3 | radio 0.1 | radio 0.3 | matter 0.1 | matter 0.3 | any m = 0.5 |
|---|---|---|---|---|---|---|---|
| 2 | 0.050 / 0 | 0.011 / 0 | 0.085 / 0 | 0.019 / 0 | 0.044 / 0 | 0.010 / 0 | ≤ 0.010 / 0 |
| 3 | **0.738 / 0.033** | 0.183 / 0.010 | **0.686 / 0.074** | 0.176 / 0.017 | **0.745 / 0.033** | 0.156 / 0.007 | ≤ 0.021 / ≤ 0.008 |
| 4 | 0.825 / 0.332 | 0.396 / 0.038 | 0.742 / 0.392 | 0.308 / 0.065 | 0.854 / 0.363 | 0.382 / 0.044 | ≤ 0.073 / ≤ 0.012 |
| 6 | 0.879 / 0.824 | 0.569 / 0.361 | 0.796 / 0.737 | 0.435 / 0.309 | 0.881 / 0.846 | 0.592 / 0.343 | 0.144–0.224 / 0.053–0.062 |

- At B = 29 the forward budget is not the bottleneck; the lossy acknowledgement is (sync fell from ~0.97 in BEAM1 to
  0.46–0.86), so beam and lockstep converge.

## Reading
The beam beats lockstep only where its 2-frame message fits and lockstep's 3-frame one does not, or fits with less
redundancy: up to 22x at B = 3, up to 10x at B = 4 (m = 0.3). With a generous budget the two are equal within 0.02.
The quick-test criterion "beam > lockstep in every cell" was set at B = 29, where they converge; it fails by one exact
tie. Not changed. A sealed version that claims what the beam adds must test it where it acts: a budget near the
message size, and P3 repair under lossy feedback, which BEAM2 does not separate from lockstep's resend.
