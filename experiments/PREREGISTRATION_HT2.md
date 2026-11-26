# HT2 pre-registration: human → AI speed with the RSOS keyboard layer (D88)

Written and committed before the owner uses the keyboard for the test. Brief: `BRIEF_HT2_KEYBOARD.md`. Baseline:
`HT1_REPORT.md` (`results/ht1_speed.json`). Instrument: `docs/keyboard.html` (commit e29417d), published as a private
artifact. Decoder brief and glossary: `experiments/ht2/decoder_glossary.md` (fixed now).

## Tasks

**T1–T6:** the six HT1 targets, unchanged (`PREREGISTRATION_HT1.md`), keyboard arm (K) only.

**N1–N4 (novel, sealed):** four new targets built only from keys that already exist, so the vocabulary was not
tailored to them. Their text is sealed in the page and shown only when a task starts. sha256 of the canonical JSON
(`[{"id":"N1","target":…},…]`, UTF-8, separators `,` `:`, no spaces) =
`a4f3c5b3cafdb080919766291781288ebb98469ba9d1aeebe479ed59ea49d583`. The plaintext is committed after the run.
Each N task is done in both arms, K and plain text (P, typed in the page), order alternating:
N1 K→P, N2 P→K, N3 K→P, N4 P→K. P = plain words, full sentences or not, the owner's choice; recorded as written.

Run order in the page: T1…T6 (K), then N1K, N1P, N2P, N2K, N3K, N3P, N4P, N4K.

## Measures (all recorded by the page, exported as JSON)

- **Time** = first key (or first typed character) to Done, in seconds. Also time from Start.
- Keystrokes (key presses, on-screen taps, typed characters, undo).
- Required slots left empty at Done.
- The message sent = the RSOS block + the plain line (K arm); the text as written (P arm).

## Decoding and scoring

- Three fresh agents, no file or tool access, the same glossary: **K-full** (all ten K messages as sent),
  **K-code** (the same ten, RSOS lines only, plain line removed), **P** (the four P messages). Messages labelled
  M1..Mn in run order. Decodes committed verbatim to `experiments/ht2/decodes.md`.
- Accuracy = share of target fields recovered. T1–T6 use HT1's field lists unchanged (`ht1_score.py`). N fields:
  each element separated by `·` or `+` in the target is one field; an operator task's first element counts as
  source, operator and host (three fields), plus direction when stated. Synonyms that keep the meaning count
  (top view = view from above). Scoring script: `experiments/ht2_score.py`, results `results/ht2_speed.json`.

## Predictions (pass rules)

- **H-A (the brief's prediction, primary).** K is faster than HT1's S **and** HT1's P on ≥ 4 of the 5 tasks that
  have HT1 times (T1–T5; T6 was untimed in HT1, so "4 of 6" in the brief can only be decided on T1–T5), **and** mean
  K-full accuracy over T1–T6 ≥ 0.95. HT1 times to beat (min of S, P): T1 10 s, T2 15 s, T3 20 s, T4 22 s, T5 26 s.
- **H-B (control for tailored keys and learning).** On N1–N4, K is faster than P on ≥ 3 of 4 tasks, and mean K-full
  accuracy ≥ mean P accuracy and ≥ 0.95.
- **H-C (does the code itself carry the meaning?).** Mean K-code accuracy over all ten K messages ≥ 0.90. If H-A
  passes but H-C fails, the gain comes from the generated plain line, not from RSOS as a code.
- Descriptive: keystrokes K vs HT1 characters; empty slots at Done; seconds per field.

## Limits fixed now

- One person, the inventor; third exposure to T1–T6 (learning effect favours K on H-A).
- The keys for T1–T6 were built from those targets (favours K on H-A; N1–N4 exist to test this).
- HT1 was self-timed with a stopwatch, HT2 is timed by the page (stopwatch reaction lag inflates HT1 times; favours K).
- The target is on screen while typing, in both arms.
- K messages include an automatically generated plain line; H-C separates its contribution.
- One decoder per arm; field scoring by the analyst, with decodes committed for rechecking.

A first measurement, not proof. Failures are reported as they come.

## Amendment 1 (17 Nov 2026, owner; before any test run): learning phase first

Owner: HT2 is not run now; the keyboard is new and needs learning first. No HT2 task (T1–T6, N1–N4) has been run;
the sealed N1–N4 have not been opened. Everything above stays in force; this adds a gate before the run.

**Learning phase.** The owner practises in the page's practice mode on the six practice targets below, never on
T1–T6 or N1–N4. The practice targets were fixed now, cover every key group (places, all seven operators,
perspective, state, reasoning, White Dragon properties, images, function, gain, trigger, all three depths, order,
all four directions) and were written not to repeat any HT2 target.

| # | Practice target (models separated by ‖) | Fields |
|---|---|---|
| P1 | White Dragon pierces the sphere · golden light + lion style · depth: structure · order 2 ‖ rocket heart heals the robot leg | 10 |
| P2 | robot head · dissociated + state of determination · contradiction · function: action ‖ rocket heart flows backward into the team · depth: inside · gain: efficiency | 11 |
| P3 | couch · moving forward = analogical reasoning, moving down = future pacing · function: decision-making ‖ sphere transplanted into the team · order 3 | 8 |
| P4 | Owl room + calculator · associated + relief · hypothesis · function: state anchor · trigger: after lunch | 7 |
| P5 | microwave palm · confidence + hologram · function: hypothesis testing ‖ microwave top · calmness · function: state anchor ‖ White Dragon beams up into the team · green particles + tiger style · depth: surface | 14 |
| P6 | Eagle room + robot leg · top view · deep work + tunnel image · function: action · order 4 ‖ the team contains the rocket heart ‖ compress the robot hand with the couch | 13 |

Fields follow the N-task rule: each element separated by `·`, `+` or `‖` is one field; an operator model counts
source, operator and host as three fields, plus direction when stated; each `direction = meaning` pair is one field.
Total 63 fields per session.

- **Practice session** = all six practice targets, in an order the page shuffles per session, each timed by the page
  as in HT2 (first key to Done). A session counts only if all six are completed.
- **Time per field** of a session = total seconds of its six targets ÷ 63.
- **Gate:** HT2 runs only when 3 consecutive counted sessions have times per field within 10% of each other:
  max ÷ min ≤ 1.10 over those three. The page computes this, logs every session, and locks the HT2 tasks until the
  gate is met. The run starts with T1 in the same sitting or the next one; the gate sessions and their values are
  reported with HT2.
- **Effect on the predictions.** Practice favours K over the untrained P arm in H-B; this is intended (the
  question is the trained keyboard against plain text) and is reported. Practice on shared keys transfers to
  T1–T6 and N1–N4; it does not expose their targets.

**Functional check before the learning phase** (owner, same message). A headless browser keys the 6 HT1 targets and
the 6 practice targets; the RSOS output must match the expected statements and compile with `src/rsoslang`, and the
plain line must carry every field. A fresh agent decodes the RSOS code only (no plain line), using
`experiments/ht2/decoder_glossary.md`. Pass: 12/12 compile and are correct, and code-only accuracy ≥ 0.90. N1–N4
are not used. Artefacts: `experiments/ht2/check/`.
