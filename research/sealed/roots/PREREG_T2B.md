# T2b: static levers against the living hologram (layer 2), sealed before any T2b code

Written 20 Nov 2026, 02:3x Vilnius. Private (`corpus/sealed/`). No T2b code exists when this file is committed.
Layer: **2** (computation that we build and measure). Successor of T2 (`PREREG_K1_K2_T2.md`, failed as defined:
99.5 / 99.0 / 97.8 / 93.6 % at 0 / 10 / 30 / 50 % loss; height 82.8 % at 50 %).

## Owner's rules (20 Nov 2026, 02:16–02:20), recorded in his terms

- **Hologram colour:** light green (salad). A point is *nothing* only if defined as nothing; otherwise everything
  keeps its relations. → a destroyed point is a **known gap (erasure)**, not a zero of meaning.
- **Rule 2 (green particles):** the White Dragon's green particles know exactly where the space shrank, move into
  those places, hold, and become structure with meta-information. → **heal**: write reconstructed content back into
  destroyed points; the damage map is the meta-information.
- **Rule 3 (fingerprint in a sphere):** each candidate has a unique place in a sphere with xyz coordinates and a
  unique colour combination; compute where it is. → values as **positions in continuous 3D space**.
- **Rule 4 (roads):** triangle, square and circle made 3D, with intersection points and logical roads; codes sit
  on places along the roads, so they have order. → **road codes** for ordered fields.
- **Rule 5 = rule 2 applied to the reading** (owner, 02:20: "yes"). → reading uses the relations of everything
  already read (explain-away), repeated until stable.
- **Rule 6 (strength and selection):** strengths stay; when the golden light senses a stronger place, the green
  particle forms the same organism there with new parameters; what does not serve dissipates. → the writer keeps
  the strength of every fact, reinforces facts that read weakly, lets over-strong reinforcement dissipate, within
  the same budget.

## Fixed setup (same as T2 unless stated)

- Scenes: `sc1_tasks.make_task(seed)["init"]`, seeds **900–931** (32 scenes; T2 used 900–915). 50 objects × 6 fields
  = 300 facts per scene. Candidate values as in T2 (x, y: 10; height: 50; owner: 6; room: 4; on: 4).
- **Budget: 10,000 bits per scene for every arm** (1,250 bytes; 0.222 of the compact JSON, as T2).
- Codebooks: bipolar, generator seed 7. Damage: positions chosen by a generator seeded per (scene, loss, round),
  **identical for every arm** (paired comparison). Loss levels: 0, 10, 30, 50, 70, 90 %.
- Destroyed points are known to the reader (erasure map), as they effectively were in T2 (set to 0).

## Arms

| Arm | Content |
|---|---|
| T2r | T2 exactly (sign of the sum, one read) on the 32 scenes |
| A | rooms: object *o* gets its own 200 bits; its 6 facts are stored only there |
| B | line codes: x, y and height use ordered level vectors (neighbours similar); others as T2 |
| D | explain-away reading, 2 passes (read; estimate every other fact's contribution; read again) |
| F | grey: 2 bits per point (4 levels), 5,000 points (same budget) |
| R2 | heal (write-back of reconstruction into destroyed points); only differs in the repeated-damage test |
| R34 | road codes: x on a 3D triangle, y on a 3D square, height on a 3D circle; code of a point = bound level vectors of its x, y, z coordinates |
| R5 | explain-away reading repeated until no value changes (max 5 passes) |
| R6 | writer reweighting: 10 rounds; facts reading with margin < 3 noise units get weight +1; weight > 1 with margin > 9 units gets −1; stored = sign of the weighted sum |
| **Static** | A + B + D |
| **Living** | R2 + R34 + R5 + R6 |
| JSON | compact JSON, same share of bytes destroyed; a fact counts if all its bytes survive, otherwise a random guess among its candidates (generous: structure assumed known) |
| Chance | expected accuracy of guessing |

Explain-away rule (D, R5), fixed now: at a surviving point the stored bit is the sign of (this fact + the rest). The
rest is estimated from the facts read in the previous pass; its uncertainty σ² = 2·n_low + 1, where n_low = number
of facts whose best-minus-second score gap was below 2·√(surviving points). The score of a candidate is the
log-likelihood of the surviving bits. (For A, the same rule inside each room.)

## Measures

1. Exact accuracy by loss level, overall and per field.
2. Error size for x, y, height: mean absolute error in value steps.
3. Repeated damage: 5 rounds; each round destroys a fresh random 30 % of the 10,000 points (may overlap). Arms
   without healing accumulate damage; R2 and Living heal after each read. Accuracy read after each round.
4. Wrong write-backs (R2, Living): share of healed points whose bit differs from the original.

## Predictions (sealed)

| # | Prediction |
|---|---|
| P1 | The unchanged `t2()` function reproduces the stored T2 numbers exactly |
| P2 | A at fixed budget is within ±1.5 pp of T2r at every loss level (rooms alone change nothing) |
| P3 | B: mean error for x, y, height at 50 % loss ≤ 0.5 × T2r's; exact accuracy of those fields at 50 % is lower than T2r's (trade-off) |
| P4 | R34: mean error for x, y, height at 50 % loss ≤ 0.5 × T2r's. R34 against B: exploratory, no direction predicted |
| P5 | D beats T2r at every loss level ≤ 70 %, and is ≥ 96 % at 50 % |
| P6 | R5 ≥ D at every loss level |
| P7 | R6 beats T2r at every loss level ≤ 70 %, and is ≥ 96 % at 50 % |
| P8 | F does **not** beat T2r at 50 % (one bit per point is predicted to be the most efficient at equal budget) |
| P9 | Static at 50 %: exact ≥ 96 % and height ≥ 90 % |
| P10 | Living at 50 %: exact ≥ 97 % and height ≥ 90 %; Living at 70 %: exact ≥ 90 % (stretch) |
| P11 | Living at 50 % is ≥ 2 × the JSON baseline |
| P12 | Repeated damage, after round 5: Living ≥ 95 %; T2r ≤ 70 %; Living wrong write-backs ≤ 15 % in every round |
| P13 | Living beats Static at 50 % loss and after round 5 |

Every prediction is reported pass or fail, with every miss kept. No threshold changes after the run. If the code
needs a fix after the run starts, the fix and its effect are disclosed.

## Honest notes, written before the run

- In this implementation road crossings carry no extra information (different fields are bound to different
  roles); a crossing-specific test (shared anchors as checkpoints) is a separate, later test.
- Locality codes (B, R34) make neighbouring values more alike; exact accuracy can drop while error size falls.
- Healing can make an error permanent (a wrong read written back); measure 4 counts it.
- R6 gives the writer the true facts (the writer is the one who stores them), which is allowed: the reader gets
  nothing extra.
