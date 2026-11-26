# PARTNERS1 (development only, owner 08:17) — road 10, pairs of coupled organisms (23 Nov 2026 ~09:15, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Dev seeds 6500, 6501; 20 bridge pairs x 2 seeds = 40 cells. Code `partners.py` (292dad6). Numbers `QUICK_PARTNERS1.json`.
PARTNERS2 checks (map K.4, 0b9af94) were written and pushed before these results were read.

| Check | Result | Pass |
|---|---|---|
| P1 joined > best organism alone | **40/40** (mean +0.0131) | yes |
| P2 joined > notubes | **20/40** (mean −0.0008) | **no** |
| P3 channels not worse than notubes | **12/40** | **no** |
Mean pair G: joined 0.9540 · notubes 0.9548 · aloneA 0.9309 · aloneB 0.9346 · native 0.9038. P4 changed the joint
action on 14.8 ticks per run.

Reading: a second organism raises the pair in every cell (the partner matters), but the tubes add nothing over two
independent organisms and worsen the worst channel in 28/40. Diagnosis (I.5): the tube view forks the whole pair with
the partner on its DEFAULTS while the partner actually runs its organism, so the shared trace is the wrong future;
and scoring the pair's mean lets one world's channel be traded for the other's G. Candidate landing for PARTNERS2's
build: the partner's own policy in the shared fork (own-future, as K.2) and per-world channel guards.
