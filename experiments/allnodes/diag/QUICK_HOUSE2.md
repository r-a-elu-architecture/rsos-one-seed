# HOUSE2 short test: Meaning with K.12 + K.16 (24 Nov 2026, commit time exact; UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Dev seeds 6640, 6641; shades 1, 4, 7, 10, 13, 16, 19 (14 cells); stress world hazard x3. Code `house2.py` (23983f2).

## Result: FAILS all 4 checks → back to step 1
| Check | Result | Pass |
|---|---|---|
| M1 house > best single object | 2/14, mean −0.0087 | no |
| M2 house > flat | 5/14, mean −0.0016 | no |
| M3 house > shuffled | 4/14, mean −0.0021 | no |
| M4 channels not worse than best single | 9/14 | no |
Mean G: house 0.9189 · flat 0.9205 · shuffled 0.9210 · single vote 0.9236 · memory 0.9217 · counter-shift 0.9210 ·
apoptosis 0.9198 · membrane 0.9184 · native 0.8722. The stress world did open a margin over the native (+0.047).

## Data for step 1
- The room selection read "overload" on 601 of 840 ticks (72 %): under stress the threshold 3 is almost always met,
  so the house ran mostly the protective room {counter-shift, membrane}, which has no choosing object (no vote).
- The single best object is the vote of futures (P8); every room that lacks it loses to it.
- Shuffled (membrane first) ties the program order: the membrane rarely changes the action in this host.
