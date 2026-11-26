# H1: predictive healing at the greatest lack

Pre-registration: `experiments/PREREGISTRATION_H1.md`. Code: `experiments/h1_predictive_heal.py`. Result:
`results/h1_predictive_heal.json` (results_sha256 `43d40999…`). 200 books, 500 steps, 20 uses per step, 20 seeds.

| Policy | First-use success | Failed first uses | Bytes per use | Round trips per use |
|---|---|---|---|---|
| R: heal after drift is caught | 0.908 | 9.2% | 98.5 | 1.18 |
| U: 5 even checks per step | 0.927 | 7.3% | 118.2 | 1.15 |
| **G: 5 checks at the greatest lack** | **0.936** | 6.4% | 114.9 | 1.13 |
| U: 10 even checks | 0.939 | 6.1% | 136.1 | 1.12 |
| **G: 10 checks at the greatest lack** | **0.951** | **4.9%** | 134.1 | **1.10** |

| | Prediction | Result | |
|---|---|---|---|
| P1 | G5 ≥ R + 0.05 and ≥ U5 + 0.03 | +0.027 and +0.008 | Fail |
| P2 | G5 bytes ≤ R | 114.9 vs 98.5 | Fail |
| P3 | G5 ≥ U10 | 0.936 vs 0.939 | Fail |

## Reading

1. **The golden light aims better than even checking, at every budget** (G5 > U5, G10 > U10 by 0.8–1.3
   points, with fewer bytes), but the gain is smaller than I predicted.
2. **Predictive healing buys speed, not bytes.** Healing ahead halves failed first uses (9.2% → 4.9% at 10 checks)
   and cuts round trips, but costs 15–36% more bytes, because some books healed ahead would not have been used
   before the next drift. Post-hoc (not pre-registered), with an 8-byte hash check instead of 60 bytes the extra
   cost is still +6% (G5) and +15% (G10).
3. **When it is worth it.** Where a failed first use is expensive (a person mid-task, an agent mid-workflow), the
   trade is good; where bandwidth is scarce, healing after the green dot catches drift is cheaper.
4. **What limited the golden light.** Lack had to be learnt from the few drifts it saw (prior Beta(1, 20)); with
   most books stable, the estimate sharpens slowly. A host that reports its own lack (the water drop: the cell
   knows it is dry) would remove that limit; that is the next variant to test.
