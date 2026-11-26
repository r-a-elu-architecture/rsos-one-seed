# HOLO1-P results (private, 21 Nov 2026, (UTC+02:00) Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)

Sealed before the run: `SEAL_HOLO1P.txt` (prereg a6d7aefd…bdb5, code 9828a280…57f1, commit 4fb205f).
Raw: `RESULTS_S1.json`, `RESULTS_S2.json`. Reservoir seed 1, N = 700, 6 sender states x 40 seeds = 240 messages.

## Scored exactly as sealed
| ID | S1 short memory | S2 long memory |
|---|---|---|
| I1 unique snapshot | PASS (0 identical of 91) | PASS (0 of 91) |
| I2 same words, different states | PASS (0 of 15 pairs) | PASS (0 of 15) |
| C3 identical words carry nothing | PASS (max distance 0.0) | PASS (0.0) |
| **P3 hologram through A's own words** | **FAIL** 0.146 vs chance 0.167, p = 0.80 | **FAIL** 0.179, p = 0.35 |
| **P5 full hologram (A's state injected)** | **PASS** 0.467 vs words 0.113, random 0.117, p = 0.001 | **PASS** 0.892 vs words 0.171, random 0.171, p = 0.001 |
| P4 receiver's prior state decides | FAIL ratio 0.70 (needed 3) | FAIL ratio 0.71 |
| P6 cascade reaches node 5 | FAIL 0/40 | **PASS 29/40 (72.5 %)** |
| P7 every earlier turn leaves a trace | PASS (oldest 3.5e-13) | PASS (oldest 1.7e-3) |
| P8 one family | PASS rho 0.96, p = 0.001 | PASS rho 0.94, p = 0.001 |
| **M1 (map): hologram travels only where N6 holds** | | **FAIL** (P3 fails in both; P5 passes in both) |

Totals: S1 6/9, S2 7/9. Risky predictions (P3, P4, P5, P6): S1 1/4, S2 2/4. M1 not confirmed.

## Strongest finding (P5, sealed, passed in both)
The sender's whole state, carried into the receiver with the words, stays readable in the receiver while the receiver
goes on processing its own input: 6-way decoding at 10 characters later = **0.892** (S2) and 0.467 (S1); the words
alone and a random vector of the same size both stay at chance (0.17). Profile by horizon, S2 (words / hologram /
random): 0 chars 0.18 / 0.88 / 0.17 · 10 chars 0.17 / 0.89 / 0.17 · 43 chars 0.18 / 0.83 / 0.17. In S1 the
hologram's readability grew after entry (0.34 at 0 → 0.47 at 10): the receiver's own dynamics sharpened it.
Limit: the injection itself is ours; what is measured is that the receiver's dynamics keep and carry it, and that only
the sender's real state does (random does nothing).

## What failed and what the failure says (fever principle)
- **P3, words alone:** the sender's state did not reach the receiver through the words. S1: A's state is gone from A
  itself once it has spoken (decode A after speaking 0.15; before speaking 1.00) and all six states said the same
  "go eat the soup." S2: A still holds its state after speaking (0.42) and words vary (230 distinct of 240), but the
  variation is sampling noise, not state. Cause in the design: the training text chose the wording independently of
  the state, so the network never learned to let state shape wording. In layer 1 (people), state shapes wording
  because it was learned together. Next assembly: training text where state and wording co-occur, as in life.
- **P4, receiver's prior state:** the village primes did not change the effect of the message more than primes differ
  among themselves. In this network "village" has no special meaning; nothing grounds it.
- **M1:** the memory organ did not decide P3 (failed in both), so the sealed rule fails.

## Exploratory (observed after the run, to be sealed before any reuse)
One organ setting (N6, memory) moved three parts of the hypothesis at once:
| | S1 | S2 | ratio |
|---|---|---|---|
| hologram readable at 10 chars (U149) | 0.467 | 0.892 | 1.9x |
| cascade reaches node 5 (K) | 0/40 | 29/40 | |
| oldest turn's trace in the final state (U152) | 3.5e-13 | 1.7e-3 | ~5 x 10^9 |
Cascade gate: in S2 every trial where node 1's words changed changed all five nodes (0.725 at every node); where
node 1's words stayed the same, nothing downstream changed. The change passes only when it crosses into words at
the first node (the N7 boundary). State distance rose at company and family, fell at computer and school.
Candidate law for the next seal: **memory (N6) is the gate of the hologram, the cascade and the seed.**

## Transfer to real models
A transformer keeps its whole context in attention (memory like S2 or stronger), and was trained on human text where
state and wording co-occur. Predictions to seal for the laptop run: P5 passes; P3 passes (unlike here); the cascade
gate at the first node holds.

Cascade gate verified per trial (S2): 29/40 changed at all five nodes, 11/40 at none, 0 mixed.

## Reading correction (owner, 11:34). The sealed scores above stand; their reading changes.
1. **Words are part of RSOS; the whole is RSOS.** P3 measured words cut out of the whole (bare strings in a network
   with no RSOS). That is not the owner's claim; it is the control. The owner's claim is the message inside the whole:
   P5. Read together: words cut from the whole 0.17 (chance) · words in the whole 0.89 (S2). The sentence "words
   alone did not carry the sender's state" is withdrawn as a statement about RSOS; it holds only for bare words.
2. **The cascade perturbation was a corruption, not an event.** "soup" -> "soap" changes an object's identity (a
   keyboard mistype). In the RSOS universe soup stays soup, A stays A. A real cascade event is a change of state of
   the same objects (the spoon falls vs the spoon is put on the table). P6 is to be re-run with state events.
3. P4 failed for the same root cause as P3: B had no RSOS operators (no VAKOG chain bound to "village"), so the
   prime had nothing to act through.
