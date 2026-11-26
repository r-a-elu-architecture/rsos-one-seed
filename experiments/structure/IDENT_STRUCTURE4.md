# Step 1 identification after STRUCTURE3: LE supply, shade 4 (24 Nov 2026 ~11:40, UTC+02:00). No build until the owner's OK.
Data: the two 60-tick LE replays of shade 4, seed 6670, rebuilt with the sealed code (diag/S3_le_v4_rep1/2.json).

| | replay 1 (learned from) | replay 2 (predicted) |
|---|---|---|
| dry onsets | 50 | 29 (-42 %) |
| supply landings by the organism | 128 | 132 (same) |
| onsets 1st half / 2nd half | 10 / 40 | 6 / 23 |
| units ever dry | 14 | 11 |
Finding: the organism acted the same in both replays (landings 128 vs 132), so the plan branch is not the gap. The HOST
differed: replay 2's world ran dry 42 % less often (50 vs 29, about 2.4 Poisson SD apart). Both replays get drier over time
(2nd half 4x the 1st). LE predicts each unit from its own past as if its tendency were fixed; it has no branch for the
host's present condition. Same direction of cause as shade 10 drift (+33 % there, -42 % here).

| Place | Missing structure | Source | Why it lands there | Check |
|---|---|---|---|---|
| LE | the HOST's present: how the world itself is running now (its onset rate so far, and its drift over time) | CLAUDE.md s1: "the host decides how a bundle behaves"; hierarchical (empirical Bayes) and adaptive renewal models: unit rate = unit tendency x host level, host level updated from what has happened so far | the unit tendency is the same in both replays; the host level is what changed | LE unchanged in form and tolerance; the prediction for each window multiplies the unit tendency (learned in replay 1) by the host level = replay 2's onsets so far / replay 1's onsets over the same ticks (only ticks before the window: a prediction, not a look ahead) |
