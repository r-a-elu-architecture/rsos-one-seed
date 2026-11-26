# H3c report: evolve-healing decided by the White Dragon filter

Pre-registration: `PREREGISTRATION_H3C.md` (committed before the run). Results: `results/h3c_filter.json`, sha256
575e6ee8bf9dcf63…. 10 seeds (500–509), 300 steps, 20 palaces × 30 books, links healed.

| Policy | Final mean quality | Copies holding a harmful version |
|---|---|---|
| Restore (copy the sender's) | −0.19 | 4.95% |
| Oracle (knows true quality, H3) | +1.51 | 0.52% |
| **Filter (measurable, new, good intention)** | **+0.67** | **0.60%** |

P1 pass (+0.85 over restore). P2 pass, **only just** (50.3% of the oracle's gain against a 50% bar). P3 pass
(harmful copies 4.95% → 0.60%, almost as low as the oracle).

## What it shows

- The White Dragon filter, using only what a real host can see, makes evolve-healing work: quality rises
  instead of decaying, and harmful versions are almost eliminated from the network (8× fewer).
- **Good intention does most of the protective work; measurability does the improving work.** The gap to the
  oracle comes from pairs where neither copy has a test (16% of pairs at 60% measurability) and from test noise.
  The lever to close it is raising the share of measurable versions: every book should carry its test.

## Limits

Simulation; the intent flag's 90% detection and the 60% measurability are assumptions, not measurements. The real
values come from the agent test (A1).
