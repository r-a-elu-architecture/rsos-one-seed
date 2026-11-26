# SEC1 v2 build 2 — real-data host (sealed run, seeds 7300-7315 x cancer/wine/digits, 48 runs)

| Prediction | wins / non-tied (of 48) | one-sided p | Result |
|---|---|---|---|
| P0 exact landing > plain SGD | 5 / 33 | 0.99999 | FAIL (reversed) |
| P2 exact > same budget global | 8 / 32 | 0.999 | FAIL (reversed) |
| P5 exact > best native | 2 / 39 | ~1.0 | FAIL (reversed) |

Mean test accuracy (exact / plain / best native): cancer 0.958 / 0.978 / 0.980; wine 0.971 / 0.976 / 0.979;
digits 0.946 / 0.946 / 0.951. Smoke seed 999 (cancer) had shown exact ahead (0.977 vs 0.959): a single seed, not evidence.

Signal (fever principle), not a verdict on the law: the build is what failed. Three build defects visible in the code:
1. The lack signal is loss x (1 + memory of errors). Memory only grows, so the landings lock onto the same
   persistently wrong examples (label noise / outliers) and keep pushing on them: the "letter" picked is the loudest,
   not the one that moves the whole.
2. The turquoise gate reads the whole on a small validation set where ties are common; ties go to the landed step,
   so the gate rarely blocks a bad landing.
3. The fork looks one step ahead, not to the end ("the letter" in HOLO6 was read against full futures).
Sealed file unchanged (D113). A corrected build is a new sealed file (sec1_real_v3), not an edit.
Blue cells: no change.
