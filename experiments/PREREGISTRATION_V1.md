# V1 pre-registration: the VAKOG key (partial-key completion)

Written before the run. Owner, 17 Nov 2026: a name is not a label; it is visual, auditory, kinesthetic, olfactory,
gustatory (VAKOG), cross-domain; anchored in a state, one channel (or two) can open the whole structure, a part
or the infrastructure, and the opened node stimulates its subnode network.

## Model (`src/rsoslang/vakog.py`)

A palace of N books; each book has a five-channel anchor (V, A, K, O, G), one symbol per channel from an alphabet
of size S, and a content hash (green dot). A cue presents k of the 5 channels; each presented channel is wrong
with probability q (noise).

| Mechanism | How it opens |
|---|---|
| A: name key | Exact lookup on one fixed channel (V, the seen name); fails when V is absent; ties broken at random |
| C: completion | Any presented channels; the book matching the most channels opens; ties at random |
| E: C + green dot | C, then the book's hash is checked against the sender's; mismatch = detected, not opened |

Runs: N = 200; S ∈ {20, 1000}; k = 1…5; q ∈ {0, 0.2}; 2,000 cues per cell; seed 20261117.

## Predictions

- P1: S = 20, q = 0, k = 2: C ≥ 0.9 and C ≥ A + 0.5.
- P2: S = 20, q = 0.2, k = 3: C ≥ 0.8 and A ≤ 0.3.
- P3: S = 1000, k = 1: C ≥ 0.95 from any single channel; A ≈ 0.2 (only when V is the presented channel).
- P4: receiver books drifted (10% of books, one channel and the content changed): C opens a wrong-content book
  silently in > 0 cues; E has 0 silent wrong opens and detects every drifted open.
- P5 (consistency check, true largely by construction): after an open, green flow with a fixed budget along
  links to subnodes removes ≥ 1.5× more deficit when it goes to the greatest lack than when spread evenly.
