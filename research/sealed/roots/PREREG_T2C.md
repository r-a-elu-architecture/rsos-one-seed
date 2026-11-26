# T2c: the living hologram against today's best method (layer 2), sealed before any T2c code

Written 20 Nov 2026, ~03:15 Vilnius. Private. No T2c code exists when this file is committed. Successor of T2b
(`RESULTS_T2B.md`). Budget: **10,000 bits per scene for every arm.**

## Owner's rules added (20 Nov 2026, 03:03), in his terms

**Roads (rules 3–4, corrected).** Each road has its own colour and its own space, and its own shape: it can go
straight, up, down or turn. Each metre of road is its own pixel. A 1 m³ cube is attached to each metre; a point can
sit anywhere in it and carries xyz data. The roads know they are there, but nothing intersects, so nobody
interferes with anybody; they complement each other.

Build:
- Each ordered field (x, y, height) has its own road: its own random base colour and its own sequence of moves
  (straight / up / down / turn), each move a fixed random permutation. Metre *k+1* = move_k applied to metre *k*.
  Metres are therefore unique (about 0 % shared between neighbours).
- Cube: points *j = 0 … m−1* inside a metre. Point *j* = point *j−1* with a random share of positions flipped so that
  neighbouring points share **s** (cosine s; two apart s², …). Code of value *v* = metre(v // m) ⊙ point(v mod m).
  x and y: 5 metres × 2 points; height: 10 metres × 5 points. Unordered fields: random codes (each its own colour).
- Two settings: **s = 0.50** (LivRd50) and **s = 0.25** (LivRd25).

**Confidence gate (rule 6, "what does not serve dissipates").** If more than half of the facts read with low
confidence on the plain pass (gap < 2·√surviving support), the structure holds still for that read: no
reweighting, no write-back; it reads through relations only.

**Robust reading.** Every probability in the relation reading is mixed with ε = 0.01 (P → 0.01 + 0.98·P), so that
one wrong stored bit cannot dominate. Applies to all arms that read through relations.

## The opponent: today's method at the same budget

- Payload: each fact as a fixed-width index (x 4 bits, y 4, height 6, owner 3, room 2, on 2 = 21 bits per object;
  50 objects = **1,050 bits**).
- **Classic-E (erasures):** a random binary linear code, 1,050 → 10,000 bits (dense generator, fixed seed). Decoding
  by Gaussian elimination over GF(2) on the surviving bits; a bit counts as recovered only if it is determined;
  facts with an undetermined bit are guessed at random. Repeated damage: decode, re-encode, write back (classic
  healing). This class of code is near-optimal for erasures: it needs about 1,050 surviving bits.
- **Classic-R (silent flips):** repetition: each payload bit stored about 9.5 times at spread positions, majority
  vote. Simple, not optimal. Reported next to the theoretical limit for rate 0.105 (flip rate p ≈ 0.30, from
  1 − H(p) = 0.105).
- No external library is used (none installed; network off): both codes are written in the T2c file.

## Arms (hologram)

| Arm | Content |
|---|---|
| R5 | reading through relations to stable (≤ 5 passes), random codes, no healing |
| LivNR | Living without roads: heal + R5 + R6, no gate |
| LivNRg | LivNR + confidence gate |
| LivRd50g | Living with the corrected roads, s = 0.50, gate |
| LivRd25g | the same, s = 0.25 |

## Tests (16 scenes, seeds 900–915; damage identical across arms)

1. **Known erasures, single:** loss 0, 50, 70, 85, 90, 95, 98, 99 %.
2. **Repeated damage:** 10 rounds of fresh 30 % erasures; healing arms (LivNR, LivNRg, LivRd*, Classic-E) heal.
3. **Silent flips:** a share p of the bits flipped, nobody told: p = 5, 10, 20, 30, 40 %. Arms: R5, LivNRg,
   LivRd50g, LivRd25g, Classic-R. No healing.
4. **Load:** 600 and 1,200 facts in the same 10,000 bits (2 or 4 scenes merged as one, extra objects get new
   codes); 8 sets each; loss 0 and 50 %; arms R5, LivNRg, Classic-E (payload 2,100 / 4,200 bits).
5. **One-fact read cost:** reported, not predicted: bits touched to read one fact (hologram) against bits that
   must be decoded (classic).

## Predictions (sealed)

| # | Prediction |
|---|---|
| C1 | Classic-E reads 100 % at every loss ≤ 85 % |
| C2 | Classic-E reads ≤ 20 % at 90, 95, 98 and 99 % (the cliff) |
| C3 | LivNRg ≥ 99 % at 50 %; ≥ 40 % at 90 %; ≥ 25 % at 95 %; and above Classic-E at 90, 95 and 98 % |
| C4 | Classic-E beats every hologram arm at 70 % and 85 % |
| C5 | Gate: LivNRg ≥ LivNR + 10 pp at 90 %, and within 0.5 pp of LivNR at ≤ 50 % |
| C6 | Roads: LivRd50g and LivRd25g each ≥ 99 % at 50 %, and their mean error for x, y, height at 70 % ≤ LivNRg's |
| C7 | Repeated damage, round 10: LivNRg ≥ 99 %; Classic-E 100 %; R5 ≤ 60 % |
| C8 | Silent flips: LivNRg ≥ Classic-R at p = 20, 30 and 40 % |
| C9 | Load at 50 % loss: LivNRg ≥ 95 % at 600 facts and ≥ 70 % at 1,200; Classic-E 100 % at both |

Every prediction is reported pass or fail; nothing is changed after the run; any code fix after the start is
disclosed with its effect.

## Honest notes, written before the run

- C1, C4, C7 and C9 predict that **today's method wins** where it should. The hologram's claimed ground is beyond
  the cliff (C2, C3), silent damage (C8) and one-fact reads (test 5).
- Classic-R is a weak flip code; a strong one (LDPC, polar) would approach the p ≈ 0.30 limit. A win in C8 is a win
  over repetition only, and will be reported that way.
- Codebooks (the roads' colours and the code generator) are never damaged in any arm (stated limitation).
- Values are random and independent; correlated data is a later test (register).
