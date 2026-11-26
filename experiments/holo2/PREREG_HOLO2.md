# HOLO2: pre-registration (private, sealed 21 Nov 2026, (UTC+02:00) Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)

Source: owner 11:50 (computer host: V sees the processor's temperature change; A hears the alarm, must cool down;
K the OS policy applied in structural order; O the kernel smells something different from before; G well fed,
working effectively and efficiently), 11:54 (order is free; the structure law does not change), U153-U158.
Layer-2 host built here (`holo2.py`): processor temperature, load cycle plus 6 heat spikes, clock speed and fan.
G-endpoint per step = work served - fan energy - overheating penalty. 120 orders x 20 seeds (100-119).

| ID | Consequence of the law | Pass rule |
|---|---|---|
| P1a | one subnode triggered (O's trace, t = 200) reaches all five subnodes | all five subnode outputs change, in all 120 orders |
| P1b | the change grows over time | median over orders of (mean divergence t 250-300) / (t 201-210) > 1 |
| P2 | the coupled structure beats parts and a plain controller on G | best order and median order beat the uncoupled parts and a PI controller, paired sign test p < 0.01 each (4 tests); best order re-checked on fresh seeds 200-219 |
| P3 | orders differ in G (order = program) | Kruskal-Wallis over the 120 orders p < 0.01 |
Recorded: computer's order (V-A-K-O-G) and person's order (V-O-K-G-A) G, top and bottom orders.
Fairness note: all controllers share actuator limits and world; the PI baseline sees temperature only; the quark
also has O's memory of the load cycle. P2 vs PI measures the whole structure, not structure alone; P2 vs uncoupled
holds the parts fixed and removes only the coupling.
