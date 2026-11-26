# RESULTS REAL3 (sealed; analyze_real3.py exactly as PREREG_REAL3.md)

97.5 % paired-t intervals (two looks).

| Row | Model | Standard | Kind | Status | Won vs standard | Result gain | Resource saved | Won vs strongest | Result gain vs strongest | Resource saved vs strongest |
|---|---|---|---|---|---|---|---|---|---|---|
| ai_agents | openrouter:meta-llama/llama-3.1-8b-instruct | react | free | SHOWN | 10/16 | +0.09375 (-0.0317, +0.219); +200.00% | +6.637 (+0.321, +13); +25.4% | 14/16 | +0.09375 (-0.0317, +0.219); +200.00% | +15.24 (+5.53, +25); +43.9% |
| ai_agents | openrouter:meta-llama/llama-3.1-8b-instruct | selfcons | free | SHOWN | 13/16 | +0.125 (+0.0114, +0.239); +266.67% | +21.99 (+12.9, +31.1); +46.5% | 13/16 | +0.1094 (-0.0173, +0.236); +175.00% | +16.87 (+8.61, +25.1); +40.0% |
| ai_agents | openrouter:openai/gpt-oss-20b | react | free | SHOWN | 7/8 | +0.1562 (+0.0263, +0.286); +20.00% | +5.777 (+1.99, +9.57); +51.3% | 7/8 | +0.0625 (-0.115, +0.24); +7.14% | +15.59 (+12.5, +18.7); +74.0% |
| ai_agents | openrouter:openai/gpt-oss-20b | selfcons | free | SHOWN | 7/8 | +0.0625 (-0.16, +0.285); +7.41% | +18.37 (+13.6, +23.1); +68.4% | 7/8 | +0.09375 (-0.0931, +0.281); +11.54% | +10.96 (+4.93, +17); +56.3% |
| ai_ai | openrouter:openai/gpt-oss-20b,openrouter:meta-llama/llama-3.1-8b-instruct | std | free | SHOWN | 7/8 | +0 (+0, +0); +0.00% | +1388 (+90.7, +2.68e+03); +36.9% | – | – | – |
| ai_human | openrouter:meta-llama/llama-3.1-8b-instruct | std | free | SHOWN | 7/8 | +0.09901 (-0.091, +0.289); +63.02% | +0.7069 (+0.442, +0.971); +41.0% | – | – | – |
| ai_human | openrouter:mistralai/mistral-small-3.2-24b-instruct | std | free | SHOWN | 8/8 | +0.2769 (+0.029, +0.525); +142.25% | +0.5971 (+0.366, +0.829); +43.6% | – | – | – |
| biology | - | std | res | UNDECIDED | 5/6 | +0.04337 (-0.0321, +0.119); +5.07% | +3136 (+2.51e+03, +3.76e+03); +90.9% | – | – | – |
| economics | - | std | res | SHOWN | 8/8 | +33.25 (+20.7, +45.8); +1.36% | -12.31 (-39.3, +14.7); -3.5% | 3/8 | +0.041 (-1.78, +1.86); +0.00% | -0.557 (-3.84, +2.72); -0.2% |
| energy | - | std | res | SHOWN | 12/16 | +0.6167 (+0.116, +1.12); +5.79% | +11 (-6.64, +28.6); +7.7% | 4/16 | -0.1751 (-0.365, +0.0148); -1.53% | -0.746 (-3.98, +2.49); -0.6% |
| neuro | - | std | res | NOT SHOWN | 4/8 | +0.007388 (-0.0153, +0.0301); +5.85% | +0 (+0, +0); +0.0% | – | – | – |
| quantum | - | std | res | NOT SHOWN | 6/16 | -0.003791 (-0.00958, +0.00199); -0.39% | +0.875 (+0.0917, +1.66); +0.0% | – | – | – |
| robotics | - | std | free | SHOWN | 7/8 | +3 (+0.482, +5.52); +1.80% | +11.11 (+3.28, +18.9); +14.3% | – | – | – |
| space | - | std | res | SHOWN | 8/8 | +7.136 (+4.35, +9.92); +1.50% | -2137 (-2.82e+03, -1.45e+03); -13.5% | 8/8 | +4.253 (+0.327, +8.18); +0.89% | -278.7 (-727, +170); -1.6% |

Stage-2 units: [('biology', '-')]
