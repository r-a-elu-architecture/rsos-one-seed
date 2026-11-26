# FUSE1 results (private, 21 Nov 2026, run 06:0x UTC after the seal e0ad7c5 was pushed)

Corpus: ChatGPT export 11 Jun 2026, 1,775 conversations; 1,688 fused and 6,573 unfused owner turns scored.

| Prediction | Result |
|---|---|
| F1 fused carry ≥ 1.5 × unfused, CI above 1 | ratio **0.76** (95 % CI 0.71–0.82): **FAIL**, and in the opposite direction |
| F2 within conversations, median > 1 | 151 conversations, 40 above 1, median **0.81**: **FAIL** |
| F3 fused decays slower | A5/A1 = 0.232 fused vs 0.234 unfused: **FAIL** (no difference) |

E8 as stated in map v1 (the owner's new words travel further in fused turns) is a **miss**.

## Exploratory, not pre-registered (labelled; to be confirmed on held-out data)
- E1: the shortfall holds at every size of the owner's addition (ratios 0.69–0.92), so it is not a length artefact.
- E2: inside fused turns, the words of the previous reply that the owner **pasted back** reappear in the next five
  replies 1.47 × as often as the words of the same reply he did not paste (0.826 vs 0.560, n = 2,728).
- Reading: re-entry steers. What the owner feeds back is amplified; what he adds new in the same turn is carried less.
  This matches the layer-1 law of E8 ("what re-enters is amplified") and contradicts the layer-2 counterpart written in
  map v1. Confound: the owner may paste the words that already mattered most (selection), which E2 cannot separate.
