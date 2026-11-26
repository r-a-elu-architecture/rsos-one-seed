# HT2 decoder brief and glossary (fixed before the run; identical for every decoder arm)

HT1's glossary text was not preserved in the repo (deviation recorded in PREREGISTRATION_HT2.md). This one is fixed
now and is given verbatim to every HT2 decoder.

## Instruction to each decoder (verbatim)

You are decoding short messages written in RSOS, a spatial-symbolic language for building mental models. Do not read
any files or use any tools. For each message M1..Mn return one JSON object with these keys (null when absent):
place, object, perspective, state, components (list), function, trigger, directions (map direction -> meaning),
operator, source, host, properties (list), depth, order, gain, other. Use only what the message says.

## Glossary

- A **place** is where a model lives: an object part (robot head, robot hand, robot leg, microwave palm, microwave top),
  a piece of furniture (couch), a room (Eagle room = view from above; Owl room = observing), or an object (calculator,
  sphere). An object inside a room is the room's **object**.
- A **model** = a perspective + a state + reasoning components, run for a **function** (e.g. decision-making, action).
- **Perspective:** associated (from inside), dissociated (from outside), top view / view from above.
- **State:** e.g. confidence, calmness, determination, relief, deep work.
- **Components:** reasoning modes (analogical reasoning, future pacing, hypothesis, contradiction) or images.
- **Directions** on an object's form: moving forward / backward / up / down carries a meaning.
- **Trigger:** the situation that selects the model.
- **Operators** act on bundles: heal, beam, pierce, transplant, flow, contain, compress. The **source** acts on a
  **host** (a person, team, object). **Properties** are the source's qualities (e.g. light colour, particles, style).
- **Depth:** surface, inside, structure. **Order:** position in a sequence. **Gain:** what improves.
- RSOS statements: `MODEL x = a + b FOR f` (model on x), `DEDICATE x TO f`, `FORM x DIRECTIONS d -> m`,
  `ROOM r PERSPECTIVE p`, `OBJECT o IN r`, `SELECTMODEL x BY trigger`, `PROPERTY x.k = v`, `HEAL host BY source`,
  `BEAM source DIRECTION d TO host`, `TRANSPLANT source TO host DEPTH d ORDER n GAIN g`.
