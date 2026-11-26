# RESULTS STRUCT1 (sealed; analyze_struct1.py exactly as PREREG_STRUCT1.md)

**LEVEL: NOT SHOWN** (0 of 5 rows: structure beats both the standard and plain rollout after Holm over 12 tests).

| Row | Model | Standard | Structure vs standard | pass | Structure vs plain rollout | pass | Full seed vs strongest (secondary) | Structure vs full seed |
|---|---|---|---|---|---|---|---|---|
| ai_agents | openrouter:openai/gpt-oss-20b | react | +5.7 % resource (CI -3.28, +4.84), result -0.0312, p=0.3326 | no | -1.6 % resource (CI -2.83, +2.44), result -0.0938, p=0.5670 | no | +63.6 % resource (CI +10, +15.8), result +0.0938, p=0.0000 | -71.7 % resource (CI -9.85, -0.761), result -0.219, p=0.9860 |
| ai_agents | openrouter:openai/gpt-oss-20b | selfcons | +42.0 % resource (CI +7.5, +15.3), result -0.0312, p=0.0001 | no | +0.5 % resource (CI -4.86, +5.02), result +0.0312, p=0.4856 | no | +45.6 % resource (CI +5.35, +14), result +0.0938, p=0.0006 | -35.9 % resource (CI -8.68, +0.371), result -0.219, p=0.9667 |
| ai_ai | openrouter:openai/gpt-oss-20b,openrouter:meta-llama/llama-3.1-8b-instruct | std | +10.6 % resource (CI -131, +793), result +0.25, p=0.0669 | no | +6.6 % resource (CI -157, +548), result +0.125, p=0.1153 | no | – | -2.7 % resource (CI -556, +409), result +0, p=0.6353 |
| ai_human | openrouter:mistralai/mistral-small-3.2-24b-instruct | std | +1.7 % resource (CI +0.00868, +0.0351), result +0.0536, p=0.0029 | no | +0.2 % resource (CI -0.00377, +0.00827), result +0, p=0.2032 | no | – | -73.4 % resource (CI -0.626, -0.432), result -0.0688, p=1.0000 |
| economics | - | std | +0.72 % (CI +9.37, +25.4), p=0.0007 | YES | +0.09 % (CI -1.82, +6.15), p=0.1195 | no | +0.02 % (CI -0.57, +1.56), p=0.1539 | -0.54 % (CI -20.7, -5.64), p=0.9978 |
| space | - | std | +0.93 % (CI +2.33, +6.87), p=0.0010 | YES | +0.34 % (CI -0.588, +4), p=0.0611 | no | +1.21 % (CI +2.71, +9.32), p=0.0018 | -0.40 % (CI -3.71, -0.266), p=0.9853 |

Rows passed: ai_agents: no, ai_human: no, ai_ai: no, economics: no, space: no
