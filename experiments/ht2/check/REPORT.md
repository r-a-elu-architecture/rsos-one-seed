# HT2 functional check (amendment 1): PASS

12 targets (T1–T6 from HT1, P1–P6 practice) keyed by a headless browser (`run_check.js`, cases and expected RSOS in
`cases.json`), compiled with `src/rsoslang` (`compile_check.py`), decoded blind from the RSOS code only by a fresh
agent (`decodes_code_only.md`), scored by `score_check.py` → `score.json`. N1–N4 not used, not opened.

| Run | Page | Correct (exact RSOS + compiles + plain line complete) |
|---|---|---|
| run1 | e29417d (as published) | **8/12**: all T1–T6 pass; P2, P3, P5, P6 fail |
| run2 | after fix | **12/12** |

**Bug found by run1 (fixed):** an operator key pressed after a finished model attached to that model and overwrote
it (P2: "dissociated" and "action" vanished; flow went from the robot head into the rocket heart). Exactly the
element-dropping the keyboard exists to prevent; T1–T6 never exercise it, so the published page would have passed a
test made of HT1 targets only. Fix: an operator joins the open frame only if it is a bare bundle/object/host;
otherwise it opens a new model. Second fix: an object part in a room (Eagle room + robot leg) no longer emits an
invalid `OBJECT robot.leg`.

**Code-only decode:** 88/89 fields = **0.989** (strict 0.978; task mean 0.992). Pass rule ≥ 0.90: **pass**.

Misses, both in the code, not the decoder:
- P2 "backward" → the grammar's FLOW/BEAM direction set has no forward/backward, so the page writes `inward`; the
  decoder read "inward". Fix candidate: add forward/backward to the direction enum in `src/rsoslang/grammar.py`
  (language core; not changed without the owner).
- P6 "contain" compiles to `WRAP … AROUND`; decoded as "wrap" (scored as kept, same meaning). Fix candidate: a
  `CONTAIN` statement or alias.

Deviation: one sentence added to the decoder instruction for messages holding several models (see decodes file).

## Practice mode (step 3)

`docs/keyboard.html` now has two modes. **Practice**: shuffled sessions of P1–P6, time per field per session
(total seconds ÷ 63), learning curve, and the gate (last 3 complete sessions, max ÷ min ≤ 1.10). **HT2 test**: the
pre-registered run order, locked until the gate is met. Sealed N1–N4 are decoded only when an N task is started.

Checks (`practice_check.js` → `practice_check.json`; regression `run3_practice_mode.json`):
- Regression: 12/12 correct again after the change.
- Three simulated sessions (60/62/64 ms per key): 18/18 keyed outputs exact; gate computed 1.046 → met; HT2 test
  locked before (start disabled) and unlocked after, first task T1; export carries sessions and gate; no page errors.
- Bug found and fixed: transplant demanded depth and gain, so P3 (transplant with order only) always logged
  2 false empty slots. Depth, order and gain are now optional for every operator (shown, marked optional).
