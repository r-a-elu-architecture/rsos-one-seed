# T11 pre-registration: population → households → market (written before running)

A re-implementation of chat 3's C3-EXP-001 (T12), whose artefacts were not captured.

**People.** 100 built persons (`identity.population`, synthetic). Each person's body is the cue framework's own person
simulator (`rsxv/sim.py` Body via `world.PersonEnv` operator sets), used read-only. One step a day for 90 days.

**Policies.**
- none: no operators;
- sham: the simulator's sham body;
- fixed calming: Bear every day;
- adaptive: Bear when distress ≥ 6, otherwise the operator set the person's profile chooses (calmness → Bear,
  drive → Tiger, regulation → Eagle).

**Households and market.**
- 25 households of 4; household tension = the members' mean distress / 10;
- 12 businesses pay wages of 60 a day to their workers;
- people spend 20 a day on essentials plus discretionary spending 25 × (1 + k × (distress − 5) / 5), with
  k = +0.3 (distress raises spending) or k = −0.3 (reversed);
- money only moves between people and businesses, so the total cash must be conserved exactly.

| # | Hypothesis (chat 3) | Pass rule |
|---|---|---|
| H1 | Cueing changes the person and propagates to households and the market | Adaptive vs none: final mean distress lower (95% bootstrap CI over persons below 0), and discretionary spending differs |
| H2 | Cash is conserved | Total cash identical to the cent on every day |
| H3 | The sign of the market effect is set by the distress → spending relation (chat: −€6,142 vs +€3,662) | The spending effect of adaptive vs none has opposite signs for k = +0.3 and k = −0.3 |
| H4 | Fixed calming vs adaptive | No prediction (chat 3: fixed better on distress, adaptive better on agency); reported |
