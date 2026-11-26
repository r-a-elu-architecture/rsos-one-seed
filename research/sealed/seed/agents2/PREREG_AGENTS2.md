# AGENTS2: do LLM agent errors belong to elements or to windows? (real LLM runs, retrospective analysis)

Written 20 Nov 2026, ~08:20 Vilnius. Private. Sealed before the analysis code. Data: the 19 A7/A8 result files and the
SC1/SC2 files in RSOS-Language `results/` (real runs; the per-step field `correct` was never analysed by position).
Retrospective: the runs exist; the analysis below has not been computed.

## Question

A one-call JSON Patch plan writes all steps of a task in one output. If its errors belong to **elements** (each step
an independent chance), the per-step error rate is flat along the plan. If they belong to a **window that grows**
(the model reading an ever more modified state, a longer output, stale values), the rate rises with the step's
position (MATH_V2 A2).

## Analysis

All JSON Patch steps (arms B2, B2s) of all files; position = step index / task length, in quartiles. Error = a step
with `correct` false. Stratified by operation kind (Mantel–Haenszel), so that position is not confounded with which
kinds come late.

## Predictions

| # | Prediction |
|---|---|
| W1 | JSON Patch per-step error rate in the last position quartile ≥ 2 × the first quartile (crude) |
| W2 | The Mantel–Haenszel odds ratio (last vs first quartile, stratified by kind) > 1.5 with a 95 % interval excluding 1 |
| W3 | RSOS blind steps (X5b): 0 errors in every quartile (known for totals; per quartile not computed) |
