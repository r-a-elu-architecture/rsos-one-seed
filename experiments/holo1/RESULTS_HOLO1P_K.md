# HOLO1-P K results (private, 21 Nov 2026, (UTC+02:00) Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)

Sealed first: `SEAL_HOLO1P_K.txt` (commit e05b90c). Event at the kitchen node: the spoon put on the table vs the spoon
falls on the floor (same objects, same identities, U155). 40 trials per system. Raw: `RESULTS_K_S1.json`, `RESULTS_K_S2.json`.

| | S1 short memory | S2 long memory |
|---|---|---|
| Event changed node-1 words | 27/40 | 39/40 |
| **Reached node 5 (school)** | **1/40 (2.5 %)** | **38/40 (95 %)** |
| K1 (S2 >= 25 %) | | **PASS** |
| K2 (S1 < 25 %, from the N6 reading) | **held** | |
| Per-node text change | 0.68, 0.20, 0.10, 0.05, 0.03 | 0.98, 0.98, 0.98, 0.95, 0.95 |
| Mean state distance per node | 2.52, 0.97, 0.25, 0.33, 0.14 | 3.02, 2.85, 3.07, 2.77, 2.89 |
| Amplify / dampen | family / computer, company, school | company, school / computer, family |

Compared with the invalid soup->soap run: S2 reach rose from 72.5 % to 95 %; S1 from 0 % to 2.5 %. A state event of
the same objects travels further than an identity corruption. In S1 the event enters node 1 in 27/40 trials and fades
node by node; in S2 it holds its size through all five nodes (state distance stays near 3).
The N6 reading (memory gates the cascade) now has a sealed pass on both sides (K1, K2); still one host, one seed.
