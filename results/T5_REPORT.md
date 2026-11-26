# T5 report: worlds and hosts

## Re-run of chat 2's same-dot / dot-combination experiments on real data

Pre-registration: `experiments/PREREGISTRATION_T5.md` (committed `5d77b8f` before running). Results:
`results/T5-DOTS.json` (results_sha256 596490fc…). Design: 288 runs, 3 real datasets, 4 dots written as
`DOT … INTO learner.training` and compiled.

| Hypothesis (chat 2) | Result | Pass |
|---|---|---|
| H1 the same bio (memory replay) dot changes sign across hosts (chat: −2.160 pp wine, +0.586 pp digits) | Cancer −0.487 pp [−1.267, +0.097]; wine 0.000 (no change in any run); digits +0.031 [−0.617, +0.710]. No interval excludes 0 | **No** |
| H2 the host decides the best combination (chat: Spearman −0.28 to −0.22) | Best differs: cancer = chem, wine = bio, digits = bio + feedback. Cancer–digits Spearman −0.297, close to the chat. Wine is constant, so its correlations are undefined, and the pre-registered mean cannot be computed | **No** (as pre-registered) |
| H3 combining is not additive | Digits: bio + feedback +0.247 pp vs sum of singles +0.031 pp, within the noise of the singles | **No** |

Baseline held-out accuracy: cancer 0.970, wine 0.982, digits 0.946.

**Reading.** With this learner, the hosts are close to their ceiling (wine 98%: no dot changes a single prediction),
and the dots' effects are within ±0.5 pp. That is too small to separate from seed noise with 6 seeds. The one
comparable number, a cancer–digits rank correlation of −0.30, matches chat 2's −0.28 to −0.22. But the
pre-registered test does not pass, and nothing is claimed from it.

**What a fair next test needs** (to be decided in review, not tuned now):
- harder hosts with headroom;
- more seeds;
- a fixed design across all three.

## World library

`examples/body_society.rsl`: the owner's body–society architecture (chat 1 T66) as a world in the language. It
contains:
- screen, circuits, cables, router = amygdala with gates, server = heart, grid, bones, muscle, spine, meta-eye;
- the information line through them;
- healing the gates;
- the heart's pulse spreading horizontally and outward;
- the rocket heart transplanted into the server.

It compiles with governance (consent, baseline for both hosts).

## T7 (communication protocol) result, for the record

`results/T7-PROTOCOL.json` (results_sha256 4f5a79bc…), pre-registered (`experiments/PREREGISTRATION_T7.md`).

| Hypothesis | Result | Pass |
|---|---|---|
| H1 structure carries meaning that names do not | Structure **98.3%** vs names 3.3% | Yes |
| H2 a third participant's accent layer leaves the carrier unchanged | 98.3% → 98.3% | Yes |
| H3 graceful with 10% of relations flipped | **47.5%** | **No**: the exact structural matcher is brittle; a tolerant matcher is the next build |
