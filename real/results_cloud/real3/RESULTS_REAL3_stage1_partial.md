# RESULTS REAL3 (sealed; analyze_real3.py exactly as PREREG_REAL3.md)

97.5 % paired-t intervals (two looks).

| Row | Model | Standard | Kind | Status | Won vs standard | Result gain | Resource saved | Won vs strongest | Result gain vs strongest | Resource saved vs strongest |
|---|---|---|---|---|---|---|---|---|---|---|
| ai_agents | openrouter:meta-llama/llama-3.1-8b-instruct | react | free | UNDECIDED | 2/8 | +0.0625 (-0.16, +0.285); +66.67% | +0.9749 (-9.54, +11.5); +12.6% | 8/8 | +0.09375 (-0.0931, +0.281); +150.00% | +25.95 (+15.8, +36.1); +79.4% |
| ai_agents | openrouter:meta-llama/llama-3.1-8b-instruct | selfcons | free | SHOWN | 5/8 | +0.09375 (-0.0931, +0.281); +100.00% | +23.55 (+4.18, +42.9); +50.5% | 6/8 | +0.1562 (-0.0306, +0.343); +500.00% | +14.12 (-2.14, +30.4); +37.9% |
| ai_agents | openrouter:openai/gpt-oss-20b | react | free | SHOWN | 7/8 | +0.1562 (+0.0263, +0.286); +20.00% | +5.777 (+1.99, +9.57); +51.3% | 7/8 | +0.0625 (-0.115, +0.24); +7.14% | +15.59 (+12.5, +18.7); +74.0% |
| ai_agents | openrouter:openai/gpt-oss-20b | selfcons | free | SHOWN | 7/8 | +0.0625 (-0.16, +0.285); +7.41% | +18.37 (+13.6, +23.1); +68.4% | 7/8 | +0.09375 (-0.0931, +0.281); +11.54% | +10.96 (+4.93, +17); +56.3% |
| ai_ai | openrouter:openai/gpt-oss-20b,openrouter:meta-llama/llama-3.1-8b-instruct | std | free | SHOWN | 7/8 | +0 (+0, +0); +0.00% | +1388 (+90.7, +2.68e+03); +36.9% | – | – | – |
| ai_human | openrouter:meta-llama/llama-3.1-8b-instruct | std | free | SHOWN | 7/8 | +0.09901 (-0.091, +0.289); +63.02% | +0.7069 (+0.442, +0.971); +41.0% | – | – | – |
| ai_human | openrouter:mistralai/mistral-small-3.2-24b-instruct | std | free | SHOWN | 8/8 | +0.2769 (+0.029, +0.525); +142.25% | +0.5971 (+0.366, +0.829); +43.6% | – | – | – |
| biology | - | std | res | UNDECIDED | 1/2 | -0.008772 (-0.53, +0.512); -0.91% | +3336 (+473, +6.2e+03); +96.7% | – | – | – |
| economics | - | std | res | SHOWN | 8/8 | +33.25 (+20.7, +45.8); +1.36% | -12.31 (-39.3, +14.7); -3.5% | 3/8 | +0.041 (-1.78, +1.86); +0.00% | -0.557 (-3.84, +2.72); -0.2% |
| energy | - | std | res | UNDECIDED | 5/8 | +0.4039 (-0.371, +1.18); +3.89% | +13.77 (-17.7, +45.3); +9.7% | 1/8 | -0.2925 (-0.608, +0.0232); -2.64% | -1.113 (-7.46, +5.23); -0.9% |
| neuro | - | std | res | NOT SHOWN | 4/8 | +0.007388 (-0.0153, +0.0301); +5.85% | +0 (+0, +0); +0.0% | – | – | – |
| quantum | - | std | res | UNDECIDED | 4/8 | -0.0004036 (-0.00645, +0.00564); -0.04% | +0.75 (-0.745, +2.24); +0.0% | – | – | – |
| robotics | - | std | free | SHOWN | 7/8 | +3 (+0.482, +5.52); +1.80% | +11.11 (+3.28, +18.9); +14.3% | – | – | – |
| space | - | std | res | SHOWN | 8/8 | +7.136 (+4.35, +9.92); +1.50% | -2137 (-2.82e+03, -1.45e+03); -13.5% | 8/8 | +4.253 (+0.327, +8.18); +0.89% | -278.7 (-727, +170); -1.6% |

Stage-2 units: [('ai_agents', 'openrouter:meta-llama/llama-3.1-8b-instruct'), ('biology', '-'), ('energy', '-'), ('quantum', '-')]
