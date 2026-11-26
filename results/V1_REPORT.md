# V1: the VAKOG key

Pre-registration: `experiments/PREREGISTRATION_V1.md`. Code: `src/rsoslang/vakog.py`, `experiments/v1_vakog.py`.
Result: `results/v1_vakog.json` (results_sha256 `d8a77828…`). Palace of 200 books, five-channel anchors.

## Opening rate (2,000 cues per cell): name key (V only) vs completion from any presented channels

| Channels in the cue | Poor channels (20 symbols), clean | Poor, 20% noise | Rich channels (1,000 symbols), clean | Rich, 20% noise |
|---|---|---|---|---|
| 1 | 0.02 vs 0.10 | 0.02 vs 0.09 | 0.18 vs **0.91** | 0.15 vs 0.72 |
| 2 | 0.04 vs 0.77 | 0.03 vs 0.53 | 0.37 vs **1.00** | 0.29 vs 0.89 |
| 3 | 0.05 vs 0.99 | 0.05 vs 0.70 | 0.55 vs 1.00 | 0.45 vs 0.97 |
| 4 | 0.08 vs 1.00 | 0.06 vs 0.84 | 0.74 vs 1.00 | 0.59 vs 0.99 |
| 5 | 0.11 vs 1.00 | 0.09 vs 0.92 | 0.91 vs 1.00 | 0.72 vs 1.00 |

Single rich channel, each alone: V 0.91, A 0.92, K 0.92, O 0.90, G 0.92: any one sense opens as well as sight.

## Checks

| | Prediction | Result | |
|---|---|---|---|
| P1 | Poor, clean, 2 channels: completion ≥ 0.9 and ≥ name + 0.5 | 0.77 vs 0.04 | Fail (threshold; gap +0.73) |
| P2 | Poor, 20% noise, 3 channels: completion ≥ 0.8, name ≤ 0.3 | 0.70 vs 0.05 | Fail (threshold) |
| P3 | Rich, 1 channel: ≥ 0.95 from any channel; name ≈ 0.2 | 0.90–0.92; name 0.18 | Fail (threshold) |
| P4 | Drift: completion opens wrong books silently; green dot stops all | 205 silent wrong opens → 0; 205/205 detected | Pass |
| P5 | Flow to the greatest lack ≥ 1.5× even flow | 1.40× | Fail |

## Reading

1. **The mechanism holds; my thresholds were too high.** Completion beats the name key everywhere, often by
   60–90 points. The misses come from collisions: with 200 books, a 20-symbol channel is shared by about 10 books,
   and even a 1,000-symbol channel collides for some books.
2. **Design rule found: the richer each sense, the fewer senses needed.** Poor anchors need three senses; rich,
   distinctive anchors open the whole from one sense (0.91) and are certain from two (1.00). In practice: each
   VAKOG anchor must be distinctive (a specific smell, a specific sound), not a generic one.
3. **Any sense works as well as the seen name.** V, A, K, O and G each open at 0.90–0.92. The name has no special
   status; it is one channel among five.
4. **The green dot is essential here too.** Completion is forgiving, so it also opens a changed book silently
   (205 times); the hash check turns all 205 into detections.
5. **Flow to the greatest lack helps, but less than predicted** (1.40×), with skewed lacks and a budget of half
   the total lack.

Known prior art: partial-cue retrieval is associative (content-addressable) memory. The new part is the
combination: one anchor declared once (`ANCHOR … CHANNEL …`, `OPEN … FROM … SCOPE whole`), used by a person's
conditioning and an agent's retrieval, with the drift check.
