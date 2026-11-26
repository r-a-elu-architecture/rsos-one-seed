# T7c pre-registration: exact first, tolerant as fallback (written before running)

T7b result: the tolerant decoder passes noise (89.2% at 10%) but loses on clean messages (93.3% < 95%). Design: try
the exact structural match first; if there is none (a noisy message), use the tolerant decoder. Same seeds.

| # | Hypothesis | Pass rule |
|---|---|---|
| H1 | Clean | ≥ 95% at 0% noise |
| H2 | 10% noise | ≥ 70% |
| H3 | Reported | 20%, 30% |
