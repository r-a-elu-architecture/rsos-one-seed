# ORG-REAL1: the family structure on real data against the field's noisy-label methods (owner "1", 22 Nov 2026 07:27)
Sealed before run. Code real6.py (imports sealed real_v5.py). Layer 1 data: cancer, wine, digits, iris (iris new) x
noise sym25 / asym30 = 8 hosts; 8 evaluation seeds each = 64 rows. Smoke: two hosts, seed 996 (code paths only).
Fixed-sequence tests (one-sided sign tests over the 64 rows, ties dropped; each step only counts if all previous pass):
 1 Control: own > rnd_own, p < 0.05.
 2 Transfer: tr > rnd_tr, p < 0.05.
 3 Primary: tr > best of the 9 baselines per row (oracle choice of the best baseline per run), p < 0.05.
Reported (not deciding): tr vs each baseline; tr on iris only (dataset never seen); tr on each noise kind; own vs best.
Colour rule: if 1-3 pass, the structure-transfer finding is confirmed in layer 1 (blue); with ORG5/ORG-FINAL in
layer 2 it becomes CYAN, and the real-data part of Level C and Biology is blue. If 1 or 2 fails: no colour change.
Disclosed: 4 datasets only (network off: the offline scikit-learn sets); iris is small (about 65 noisy training
examples, 45 test); the noisy-label methods are linear-model versions of co-teaching, small-loss and confident
learning, and are given the true noise rate.
