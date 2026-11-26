# H3c pre-registration: evolve-healing decided by the White Dragon filter

Written before the run. Option 3 of 17 Nov 10:21, approved 10:24 ("yes all of the things are done today").
H3's evolve policy knew each version's quality. Here "better" is decided only by what a real host can see:
the White Dragon filter (measurable, new, good intention).

## Model (`experiments/h3c_filter.py`, same network as H3: 20 palaces, 30 books, links healed)

Each edit makes a new version with hidden quality change N(−0.01, 0.1). 5% of edits are harmful: change
N(−0.5, 0.1), and carry a bad-intent flag that the filter detects with probability 0.9. Each version is
measurable (has a test) with probability 0.6; a test reads quality with noise sd 0.15. When two copies differ:

| Policy | Rule |
|---|---|
| B restore | receiver takes the sender's version |
| C oracle | keep the higher hidden quality (H3) |
| C filter | drop any copy flagged bad intent; of the rest, if both measurable keep the higher test score, if one is measurable keep it, if none restore (sender's); new = the version differs from the receiver's |

300 steps, 10 seeds (500–509).

## Predictions

- P1: final mean quality: filter ≥ restore + 0.5.
- P2: filter captures ≥ 50% of the oracle's gain over restore.
- P3: share of copies holding a harmful version at the end: filter ≤ half of restore.
