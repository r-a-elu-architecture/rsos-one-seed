# H3 pre-registration: healing that evolves, and healing of connections

Written before the run. Owner (17 Nov, verbatim): the White Dragon heals "for evolving transforming signaling and
making humanity better"; it can "heal connection between the universes". Understanding v2, rows 7–8.

## Model (`experiments/h3_evolve_links.py`)

20 palaces, 30 books, every palace holds its own copy of every book (version, quality). Each pair of palaces has
a link with a codebook on each side (the shared conventions of that connection). Per step: each book copy is
edited locally with probability 0.02 (new version; quality changes by N(−0.01, 0.1), so edits improve or degrade);
each side of each link drifts with probability 0.01. 50 messages per step between random pairs on random books.
A message is delivered when, after any healing, both sides hold the same book version and the same link codebook.

| Policy | Book heal (green dot catches a version mismatch) | Link heal |
|---|---|---|
| A restore, no link heal | receiver takes the sender's version | none: a link mismatch makes the message fail |
| B restore + link heal | receiver takes the sender's version | link hashes compared; receiver takes the sender's codebook |
| C evolve + link heal | both take the better of the two versions (quality measured with noise 0.02) | as B |

300 steps, 10 seeds.

## Predictions

- P1: delivery: B ≥ A + 0.05.
- P2: final mean book quality: C ≥ B + 0.10 (absolute), with delivery within 0.01 of B.
- P3: quality trend over the last 200 steps: B slope ≤ 0.0005 per step; C slope > 0.
