# BEAM3 development check of the K.3 sealed form (23 Nov 2026 ~08:45, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Development seeds 6480, 6481 (channels 6490+); does not count. Numbers: `QUICK_BEAM3_6480_6481.json`.

| Check (K.3) | Result | Pass |
|---|---|---|
| C1 beam > lockstep at B = 3 and 4, every cell | **18/18** (e.g. B3 light 0.1: 0.734 vs 0.033; B4 radio 0.3: 0.297 vs 0.064) | yes |
| C2 no wrong adoption; zero-loss exact, sync 1.0 | 0 wrong; 42/42 exact; 42/42 sync 1.0 | yes |
| T29 declared tie | max |beam − lockstep| = 0.023 | (reported) |
| C3 P3 repair > whole resend at B = 3 and 4 | **7/18** | **no** |

## Diagnosis of C3 (binding error in the P3 arm, and a finding about the beam)
- The P3 arm's feedback carries only the latest applied tick. When an acknowledgement is lost the sender cannot know
  which parts arrived, so it spends the budget re-sending parts the receiver already applied. "Repair only the
  missing parts" needs the receiver to say which parts are missing (the syndrome travels back), which this build
  does not do.
- Finding: the "whole" control streams (it sends the bundle of all unacknowledged parts every tick, without waiting),
  and at B = 29 it holds sync 0.93–0.98 against the beam's 0.46–0.86. The beam and lockstep arms of beam2.py wait for
  an acknowledgement before the next message (stop-and-wait); under lossy feedback that wait, not the carrier, is
  their limit. Both points belong in the next build before the seal; the K.3 checks are not changed.
