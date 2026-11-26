# RESULTS REAL1 (sealed; analyze_real1.py exactly as PREREG_REAL1.md)

| Row | Model | Standard | Kind | Cells won | Result gain (95% CI) | Resource saved (95% CI) | Shown |
|---|---|---|---|---|---|---|---|
| ai_agents | openrouter:openai/gpt-oss-20b | react | free | 7/20 | +0.0375 (-0.0496, +0.125); +5.00% | -0.218 (-2.25, +1.82); -1.6% | no |
| ai_agents | openrouter:openai/gpt-oss-20b | selfcons | free | 13/20 | -0.0125 (-0.141, +0.116); -1.59% | +12.5 (+11, +14); +47.1% | no |
| ai_ai | openrouter:openai/gpt-oss-20b,openrouter:meta-llama/llama-3.1-8b-instruct | std | free | 16/20 | +0.1 (-0.0438, +0.244); +13.33% | +474.9 (+32.1, +918); +13.0% | YES |
| ai_human | openrouter:meta-llama/llama-3.1-8b-instruct | std | free | 15/20 | +0.06924 (-0.00566, +0.144); +45.01% | +0.0222 (+0.0123, +0.0321); +1.3% | YES |
| ai_human | openrouter:mistralai/mistral-small-3.2-24b-instruct | std | free | 13/20 | +0.09347 (+0.0109, +0.176); +88.07% | +0.01145 (-0.00129, +0.0242); +0.9% | no |
| biology | - | std | res | 16/20 | +0.06344 (+0.0365, +0.0904); +7.76% | +1.5 (-1.63, +4.63); +0.0% | YES |
| economics | - | std | res | 20/20 | +14.82 (+11.2, +18.4); +0.61% | -1.308 (-7.65, +5.04); -0.4% | YES |
| energy | - | std | res | 18/20 | +0.8555 (+0.476, +1.23); +7.81% | -1.782 (-15.3, +11.7); -1.2% | YES |
| quantum | - | std | res | 9/20 | -2.913e-05 (-0.00535, +0.00529); -0.00% | +0 (+0, +0); +0.0% | no |
| robotics | - | std | free | 12/20 | +2.35 (-0.802, +5.5); +1.44% | +4.288 (-1.76, +10.3); +5.2% | no |
| space | - | std | res | 20/20 | +6.043 (+5.24, +6.84); +1.17% | -1610 (-1.76e+03, -1.46e+03); -10.0% | YES |
