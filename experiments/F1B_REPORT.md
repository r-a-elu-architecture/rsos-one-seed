# F1b report: the feedback loop scored fairly

Pre-registration: `PREREGISTRATION_F1B.md` (committed before the run). Results: `results/f1b_feedback.json`, sha256
daf7caf1766b07c2…. 10 seeds (700–709), 6 generations, 1,200 landings per generation, no frontier cap.

| Loop | Useful share (vs original parent) | CV of useful count | Root deficit drop |
|---|---|---|---|
| Open | 0.230 | 0.19 | 0 |
| Weights only | 0.248 | 0.27 | 0 |
| Weights + parent healing | 0.248 | 0.27 | **0.22** |

P1 fail (+0.018, bar +0.05). P2 fail (+0.018, bar +0.03). P3 fail (feedback is *less* steady). P4 pass.

## Verdict on the feedback series (F1 + F1b)

- Scored fairly, the earlier halving disappears: parent healing costs nothing and improves the 48 roots by 0.22.
- **Reinforcing domain entries is a weak lever in this engine** (+0.02 useful share) and makes growth less
  steady, because it concentrates landings and the frontier swings with it. What limits usefulness is structure:
  about a quarter of all landings repeat a signature already seen.
- So the cybernetic loop that works is **children → parent → root** (the node gets better). Entry reinforcement is
  not worth keeping as is. If the engine is revisited, the lever is novelty: steer landings away from signatures
  already seen, not toward entries that paid before. Not pursued now: A1 comes first.
