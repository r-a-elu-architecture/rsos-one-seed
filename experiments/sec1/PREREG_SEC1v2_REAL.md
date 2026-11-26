# SEC1 v2 build 2: real-data host (T5 data), under TOP_MAP_SEC1_v2.md

Sealed before the run. Fresh seeds 7300-7315 x {breast cancer, wine, digits} (48 runs), 300 steps of 16, budget 4
landings per step. P0 exact > plain SGD; P2 exact > the same budget spread globally (rate x 1.25); P5 exact > best of
plain, decaying rate, online hard-example mining. Measure: test accuracy at the end. One-sided sign test over the 48
runs, ties dropped (standard sign test). P1, P3, P4, P7 not measurable here. Smoke on seed 999 (outside the test)
only checked that the code runs and timed it. This is the real-data host: it is the one that can move blue cells.
