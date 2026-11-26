# SEC1 v3: corrected builds (organism + real data), sealed before run

Owner said "seal" (21 Nov 2026, 14:53). Sealed v2 files untouched (D113); v3 files import them with a hash check.
Organism v3 (sec1_org_v3.py): shared gain instead of veto; the organism reads its own program, the hosts' own
programs and the default as whole futures and lands the best whole. Fresh seeds 7400-7415 x densities 1-5 (80 worlds).
Predictions as v2: P0, P1, P2, P3, P5, P7; one-sided sign tests, Holm over the six. Disclosure: the hosts' own
programs are inside the organism's candidate set.
Real data v3 (sec1_real_v3.py): fading memory, strict whole on validation log-loss + per-class accuracy, 20-step
future horizon on common batches. Fresh seeds 7500-7515 x cancer/wine/digits (48 runs). P0, P2, P5.
Smoke on seed 999 only checked that the code runs and timed it (real: cancer 0.959, 31 landings kept); nothing tuned.
