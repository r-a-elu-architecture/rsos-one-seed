# HT1 report: human → AI communication speed, owner's symbols (S) vs plain text (P)

Pre-registration: `PREREGISTRATION_HT1.md` (commit 23d2995, before the owner wrote anything). Messages verbatim:
`experiments/ht1/owner_messages.md`; decodes: `experiments/ht1/decodes.md`; scoring: `experiments/ht1_score.py`,
`results/ht1_speed.json` (sha256 e1f8266b…).

| Task | Time S | Time P | Chars S | Chars P | Accuracy S | Accuracy P |
|---|---|---|---|---|---|---|
| T1 robot head | **10 s** | 12 s | 71 | 70 | 0.80 (function missing) | 1.00 |
| T2 robot hand | 19 s | **15 s** | 68 | 54 | 1.00 | 1.00 |
| T3 couch | **20 s** | 25 s | 46 | 66 | 0.75 ("contradiction" missing) | 1.00 |
| T4 Eagle room | 42 s | **22 s** | 47 | 79 | 1.00 | 1.00 |
| T5 microwave | 28 s | **26 s** | 75 | 79 | 0.75 | 0.75 |
| T6 rocket heart | — | — | 72 | 93 | 1.00 | 1.00 |
| Total / mean | 119 s (T1–T5) | 100 s | 379 | 441 | 0.88 | 0.96 |

**K1 fails: 0 of 5 timed tasks** where S was both faster and at least as accurate (T6 untimed cannot change this).

## What it shows

- **Protocol deviation that changes the reading:** the owner wrote P as shorthand on every task, not as full
  sentences. HT1 therefore compares two compressed forms by the same person, not RSOS symbols against ordinary
  language. Both were short (379 vs 441 characters) and both decoded well (0.88 vs 0.96).
- **Free-typed symbols lose elements.** Where S was faster (T1, T3), it dropped an element (the function; the
  word "contradiction"), and accuracy fell. Speed came from omission, not from a better code.
- **Typing is the bottleneck, as the owner said during the test (D88).** The symbols had to be spelled out
  letter by letter; the S arm had no input advantage over P. This is the direct case for the keyboard layer: fixed
  keys that emit complete components (no element can be dropped) at the speed they are seen.
- **First attempt (T1, attempt 1, verbatim):** the owner first described the execution layer (hologram, relief in
  the body, the lion, the particle appearing when VAK fires), not the model's specification. The language carries
  what happens when a model runs; a test of transmission must state which layer it measures.

## Limits

One person (the inventor), self-timed, tasks from his own models, one decoder per arm, scoring by field match
(decodes committed for rechecking). A first measurement, not proof.

## Next

HT2 (D88): the same six targets entered with an RSOS keyboard layer, against HT1's S and P times and accuracy.
Pre-register before building the prototype's final version.
