# ORG-REAL1 results (sealed f80259e; analyze_real1.py exactly as PREREG_REAL1.md; full print out_real1.txt)
Fixed sequence: 1 control own > random: 34/47, p 0.0015 PASS (first clean real-data control pass).
2 transfer tr > random: 35/41, p 2e-6 PASS. 3 primary tr > best of 9 baselines chosen per run (oracle): 31/57,
mean -1.8 pts, p 0.30 FAIL. By the sealed colour rule: no colour change, no cyan.
Against each method separately, the transferred structure wins every comparison: plain 55/62, decay 58/61, ohem
55/63, small-loss 43/55 (p 2e-5), small-loss+decay 42/58, co-teaching 46/57 (p 2e-6), co-teaching+decay 41/57,
confident learning 46/60 (p 2e-5), CL+decay 43/60 (all p < 0.001). Mean test accuracy: transferred structure 0.855;
best single method 0.838 (small-loss+decay); oracle best-of-9 per run 0.872.
Family structure in layer 1: the transferred structure is the same on all 8 hosts (barrier + detect + memory + reg,
'11011'), and it is also the host's own best on 5 of 8.
Signal: iris (new, about 65 noisy training examples) 2/13 vs the oracle: the barrier (memory > 3) removes too much on
tiny data. By data vs oracle: wine 11/13 (p 0.011), cancer 11/16, digits 7/15, iris 2/13.
Note for the next seal: the oracle-of-9 bar is stricter than the field's usual comparison (against each method);
any change of rule needs fresh seeds.
