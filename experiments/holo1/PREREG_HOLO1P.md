# HOLO1-P: pre-registration (private, sealed 21 Nov 2026, (UTC+02:00) Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)

Source: owner 10:46 (whole-state snapshot, hologram message; U148-U152), owner 11:16 ("first we do it here and see
the test here; if we are able to do it here, then we transfer it to the real tests on real models").
Design parent: `PREREG_HOLO1_DESIGN.md` (H1-H8). This is the in-workspace pilot (P) of that design.

## Layer-2 system
A character-level recurrent language network built here in numpy (`holo1p.py`): echo-state reservoir with a trained
ridge readout (next character). Its whole state at each character is one vector: frozen, copied, injected, compared
exactly. A and B are two copies of the same network. The training text is neutral: in it, the wording of the soup
message is chosen independently of the sender's state, so any trace of the state in the words must arise in the
network, not be taught.

Two organ settings (node N6, memory), both sealed, both run with reservoir seed 1, N = 700:
- **S1 short memory:** leak 0.5, spectral radius 0.95.
- **S2 long memory:** leak 0.15, spectral radius 0.99.

## Map-aimed prediction (the row-2 kind: the map says where it travels)
**M1:** the hologram travels where memory (N6) holds the state across the cue: P3 and P5 pass in S2, and do not
pass in S1. M1 holds only if both halves hold.

## Predictions (each system scored separately)
| ID | Hypothesis part | Pass rule |
|---|---|---|
| I1 | U148 unique snapshot (instrument) | 0 identical consecutive snapshots |
| I2 | words produced by the whole state (instrument) | 0 identical pairs of A-states after the same sentence |
| C3 | control: identical words carry nothing | max distance between B-states under identical words = 0 exactly |
| P3 | **U149 + O: hologram through A's own words** | B-state decodes A's state above chance, permutation p < 0.01 (6 states x 40 seeds, nearest-centroid, 5-fold) |
| P5 | **U149: the full hologram** (A's pre-utterance state injected into B with the words) | at 10 chars after: acc(hologram) >= acc(words) + 0.10 and >= acc(random vector, same norm) + 0.10, and perm p < 0.01 |
| P4 | G (U146): the receiver's prior state decides the effect | effect (village vs neutral primes, mean state change) / noise floor (within-group splits) >= 3 |
| P6 | K + U152: cascade kitchen -> computer -> company -> family -> school | a one-character change ("soup" -> "soap") at node 1 changes node 5's text in >= 25 % of 40 trials; which nodes amplify or dampen is recorded |
| P7 | U152 infinite seed | every one of 8 earlier turns has a non-zero effect on the final state (float64); decay profile recorded |
| P8 | U151 one family | mean cross-domain RDM Spearman above shuffled-template null, p < 0.01 |

## Disclosed before sealing: dev run (seed 999, N = 300, S1 only, not reported as a result)
Used only to check the code runs. It showed: P3 chance (0.15), P5 chance, P4 ratio 0.66, P6 0/12, P7 all non-zero
(oldest turn 2e-12), P8 0.97 (p = 0.001), C3 = 0. A's state decodes 1.0 before speaking and at chance after.
Changes made after dev, all mechanical or design-level, none to pass rules: exact-distance control for C3; memory-
efficient training; H5 injects the pre-utterance state (the state that produced the words, as the owner's model
says) and records horizons 0/5/10/20/43; the S2 system was added. S2 was not run before sealing.
P8 is weak evidence: dev shows the shared structure comes from shared sentence frames (grammar).

## Scope
This is layer 2 in a small network, not a real language model. A pass shows the mechanism exists in a layer-2
system and fixes the kit; a fail is a signal (fever principle) for the next assembly. Transfer next: the same
code paths on an open model on the owner's laptop (hidden states via transformers).
