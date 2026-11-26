# AGENTS2 results (real LLM runs, retrospective analysis), private

Predictions: `PREREG_AGENTS2.md` (commit efc19ec, before the code). Code: `agents2.py` (before any result). Data:
`RESULTS_AGENTS2.json`. Input: 25 result files in RSOS-Language `results/` (A7/A8 and SC1/SC2/SC2-C, as the
pre-registration's glob defines). Run 20 Nov 2026, ~08:25 Vilnius; 0 model calls.

## Strongest finding

**In real LLM agents, one-call JSON Patch errors belong to a growing window, not to independent steps.** The per-step
error rate rises along the plan:

| Position in the task | first quarter | second | third | last quarter |
|---|---|---|---|---|
| JSON Patch error rate | 0.19 % (9 / 4,630) | 0.49 % | 1.56 % | **2.33 % (104 / 4,470)** |
| RSOS blind error rate | 0.08 % | 0.16 % | 0.10 % | 0.11 % |

Controlling for the kind of operation (Mantel–Haenszel), the odds of a wrong step in the last quarter are **12.3×**
those in the first (95 % interval 6.1–24.7). The same law that governs the real database (MATH_V2 A2: failure follows
the windows an operation spans) describes where language models break: late in a long plan, on a state they have
already changed. Blind planning, which never reads the state, stays flat.

## Predictions: 2 pass, 1 fail

| # | Result |
|---|---|
| W1 last quarter ≥ 2 × first | **pass**: 12.0 × (2.33 % vs 0.19 %) |
| W2 stratified OR > 1.5, interval excluding 1 | **pass**: 12.27 (6.09–24.73) |
| W3 RSOS blind: 0 errors in every quarter | **fail**: 17 wrong steps, **all 17** in the SC2-C control (two tasks; the published capped control, FAILURES_MAP #51); 0 in every other file |

## Diagnostic (after the result)

Without the SC sets (A7/A8 only), JSON Patch rises from 0.03 % (1 / 3,328) to 0.28–0.45 % in the later quarters: the
same direction on fewer errors. The SC sets (300 keys, 56 steps) carry most of the effect, as their longer plans
predict.
