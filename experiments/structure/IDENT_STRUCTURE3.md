# Step 1 identification after STRUCTURE2 (24 Nov 2026 ~11:15, UTC+02:00). No build until the owner's OK.
Data: STRUCTURE2 traces, shade 10 (diag/l6local_p1.json.gz, RESULT_STRUCTURE2.json).

## Findings from the traces
- LE window 8, shade 10, drift: NOT a cascade. Of 20 drift onsets in 8-tick windows (structure arm), 0 had a drifted
  neighbour at the window start and 1 had one later in the window; 19 had none. The relation is not the missing branch.
  Replay 1 holds 18 drift onsets (share 0.038); replay 2 holds 24 (0.048): +33 %. LE learns each unit's tendency from a
  30-tick past with 18 events and its tolerance counts only replay-2 noise, not the noise of what was learned.
- D shade 10: parents in the child host A 0.9272, B 0.9353; child 0.9333, between them. The child took A's present action
  in 21 of 30 ticks although B is the better parent: each option is valued by replaying a PARENT's plan, but afterwards the
  child does not follow that plan; it chooses again. Its value is measured in a future that is not its own.

| Place | Missing structure | Source | Why it lands there | Check |
|---|---|---|---|---|
| LE (law of error events) | the PAST branch is too short: a unit's tendency learned from 30 ticks (18 events) | the time-as-structure rule found this morning (16-tick seed cut branches; D flipped); renewal theory: residual-life estimates need the event count, not the tick count | replay 2 differs from replay 1 by +33 % events by chance; no relation or plan explains it | LE prediction carries its own uncertainty from the past it learned (event count of replay 1) in the tolerance; or the seed holds enough events (60 ticks, as LAWS6: 37/42 there). Owner's choice |
| D (child) | the child's OWN future: its value is measured in its parents' plans, not in its own trajectory | K.2: need is measured in the organism's own future with its own policy; the owner (09:54): each unit holds its own past, present, future | where the parents differ (shade 4) a parent's plan is close enough (+0.023); where they are close (shade 10) the mismatch decides (-0.002) | value each option by the child's own continuation: the child's recorded choices (its own lineage time) as the plan it replays |
