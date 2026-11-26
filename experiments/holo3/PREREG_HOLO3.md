# HOLO3: pre-registration (private, sealed 21 Nov 2026, (UTC+02:00) Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)

Source: owner 12:31 ("hot" = the space of possibilities in relations and connections; every state New, Ready,
Running, Waiting, Terminated, Suspended is a quark with VAKOG, sub-VAKOG, recombinations, and keeps its structural
logic), 11:50 (computer reading of V, A, K, O, G), 11:54 (order is the program; the law does not change).
Host (`holo3.py`): OS process lifecycle with 7 states, 8 memory slots (suspension), one CPU (quantum 4), one shared
I/O device. Relation density d = 1..5: 10d processes, dependency probability 0.1d, arrivals over 40d steps.
G-endpoint = -(mean slowdown). 120 orders x 5 densities x 8 seeds (300-307).
Baselines: round-robin (longest-waiting first) and history (exponential burst estimate, shortest first: an O-like
standard). Uncoupled quark: the same five parts, each from the raw signal, summed.

| ID | Consequence | Pass rule |
|---|---|---|
| P2 | **hot = relations: the structure's advantage grows with relation density** | advantage (median order minus best baseline, per seed) at d = 5 > at d = 1, and Spearman(d, advantage) > 0 with p < 0.05 |
| P2b | the chain itself matters under stress | coupled median order beats uncoupled at d = 5, sign test p < 0.05 |
| P3 | the law under recombination | a trigger on O of one process (t = 60, d = 5) changes all five of its subnodes in all 120 orders; other processes changed recorded |
| P1 | same structure at two levels | Spearman between the 5x5 subnode correlation at process level and at system level (per-window aggregate) above label-permutation null, p < 0.01 |

Disclosed before sealing: a smoke run (`--quick`, 6 orders, seeds 300-302) printed P1 on seed 300, which is also the
main run's P1 seed: p = 0.096 (below the bar). P1 is therefore not a blind prediction and is reported as seen.
Its system level also shares the subnode definitions (it aggregates them); a pass would be weak evidence either way.
P2, P2b and P3 values were not seen. Fairness: the quark uses relation information (dependents waiting) by design,
as O is defined (traces of every part it touched); the baselines do not. P2b holds information fixed.
