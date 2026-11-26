# Q1 quick test: is every change a structural change that can be named and found? (exploratory, 22 Nov 2026)

Map Part 0.8a. 13 quarks (root → 3 nodes → 9 subnodes), V A K O G per quark in its own order, tubes carrying G, noise.
One change per world, of four types the readers never saw; 50 worlds per type. STRUCTURE reader knows the generator, not
the change; BLIND reader has no structure. No colour depends on these runs (development seeds only).

| Run (seeds) | Reader | Located | Type named | kick | order | operator | relation (located) |
|---|---|---|---|---|---|---|---|
| Q1 (100–299), prediction fixed before the run | structure | **163/200 (82 %)** | **200/200** | 13/50 | **50/50** | **50/50** | **50/50** |
| | blind | 63/200 (32 %) | 50/200 (25 %) | 1 | 3 | 23 | 36 |
| Q1b (300–499): onset read per subnode for every type | structure | 123/200 | 159/200 | 4 | 38 | 42 | 39 |
| Q1c (500–699): kick read as one subnode's spike | structure | **174/200 (87 %)** | 175/200 | 24/50 | **50/50** | **50/50** | **50/50** |
| | blind | 48/200 (24 %) | 50/200 | 4 | 3 | 17 | 24 |

Prediction (Q1): structure ≥ 80 % located and ≥ 70 % typed; blind ≤ 50 % located, type ~25 %: **PASS** (located only
just: 82 %). Q1b made things worse (per-subnode onset fired on noise) and is kept as a record.

Reading: every **persistent** structural change (order, operator, relation) was named and found: 300/300 across Q1 and
Q1c, against 3–72 % for the blind reader. **One-time** changes (a kick) were found in only 13–24 of 50: a transient
leaves a momentary trace, and the reader compares hypotheses without accounting for how much each can absorb noise.
Next fix (not run): weigh each hypothesis by its freedom, and keep the O trace per subnode across time.
Limits: layer 2, and the structure reader knows the true generator, so success is partly by construction; what the
test shows is that the structure adds locating power the blind reader lacks, and where it still fails.
