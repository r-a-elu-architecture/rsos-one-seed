# PREREG MAP1: does the sealed map pair the right things? (private, 21 Nov 2026)

Tests map/MAP_VAKOG_V1.md (sealed 08:24) at its own level: the 15 nodes, both layers.
Stage 1, `mechanisms.py` (the layer-2 mechanism of each node, quoted from the map's turquoise A and K columns), was
sealed and pushed **before any host existed** (commit e68eec0, sha256 3c87c3f2…ae24b8ae).
Stage 2, `hosts.py` (the layer-1 host of each node, a standard textbook form of the blue row) and this file are sealed
by the next commit, pushed **before any run**. `run_map1.py` is part of that commit.

## Design
- 15 mechanisms × 15 hosts = 225 pairs; 30 episodes per pair (seeds 1000–1029), 200 steps each.
- Objective per episode (lower is better): mean harm + 0.2 × mean intervention. Same for every pair.
- **Matched** = node i's mechanism on node i's host. **Mismatched** = the 14 other mechanisms on that host.

## Predictions
- **P1 (primary):** on at least **11 of 15** hosts, the matched mechanism scores better than the median of the 14
  mismatched mechanisms.
- **P2 (primary, significance):** the sum over hosts of the matched mechanism's rank (1 = best of 15) is lower than in
  at least 95 % of 10,000 random assignments of mechanisms to hosts (one-sided permutation p < 0.05, seed 21112026).
- MAP1 **passes** only if P1 and P2 both pass.
- Reported, not predicted: each host's matched rank; matched vs no intervention (u = 0) and vs always on (u = 1).

## What each outcome means (decided now)
- Pass: the map's pairings are not arbitrary: the mechanism read from the AI layer of a node is the one that serves the
  real-world process of the same node, more than the mechanisms of other nodes. The higher-order structure holds on
  this test, and lower-level tests can be aimed by it.
- Fail: on this test the pairings do no better than chance; the map is not confirmed; each node's rank shows where it
  breaks, and map v2 records it.

## Limits, stated now
- The hosts are established laws run in code, not new measurements of the world.
- The same assistant wrote mechanisms and hosts. Guards: mechanisms sealed first; hosts are standard forms; the
  shuffle control (P2) asks whether *the pairing* matters, not whether a mechanism is good in general.
- Several mechanisms are threshold rules; if they behave alike, matched and mismatched will look alike and P1/P2 fail.
