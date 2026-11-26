# ORG-REAL2 results (sealed 93aed9e; analyze_real2.py exactly as PREREG_REAL2.md; full print out_real2.txt)
1 control own > random: 38/43, p 1e-7 PASS. 2 transfer tr > random: 35/47, p 5e-4 PASS.
3 primary (beat each of 9, Holm): FAIL. Wins vs plain 53/60, decay 54/61, ohem 56/61 (Holm < 1e-6); ties or loses vs
the noisy-label methods: small-loss 29/61, small-loss+decay 22/59, co-teaching 29/60, co-teaching+decay 24/58,
confident learning 35/57 (Holm 0.33), CL+decay 26/59. Mean accuracy: tr 0.803; small-loss+decay 0.819; co-teaching+decay
0.808; per-run best of 9 0.849. No colour change, no cyan.
Cause (design error, mine): the size-scaled barrier was capped at 20 % of the training set, BELOW the noise rates of
these hosts (25 % and 30 %), so the barrier could no longer remove the noise it found; the structure's edge over the
noisy-label methods in ORG-REAL1 came largely from the uncapped barrier. Iris still loses (0/12 vs best of 9).
Replicated in layer 1 across ORG-REAL1 and ORG-REAL2: control (34/47; 38/43) and transfer (35/41; 35/47): a structure
found on other real datasets beats a random structure of the same size. As sealed, no further seeds on this line.
