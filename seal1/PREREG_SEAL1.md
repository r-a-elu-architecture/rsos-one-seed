# PREREG SEAL1: the combined sealed run, layer 2 (24 Nov 2026 ~06:00, UTC+02:00 Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)
Written and pushed before any SEAL1 seed is run. Owner's decisions: K.5 (24 Nov 00:12–12:27), the advice accepted
24 Nov 04:45 ("seal now without Meaning, D, E; Law 4 noise-free check on 11 shades; build the heterogeneous host here
while the laptop runs"). Code hashes: `SEAL_SEAL1.txt` (checked by `seal1.py` at start; a changed file stops the run).
Colours come only from this run (Layer Rule). Development results are not evidence here.

## Rows in this seal and what decides each colour
| Row | Build (unchanged from its development pass) | Fresh seeds | Turquoise iff |
|---|---|---|---|
| **8 · Physical layer and first beam** | `beam6.py` (K.10; claim K.3: structure-coded lockstep) | worlds 5350, 5351; channels 536000+ | K.3 all: C1 beam > lockstep at B = 3, 4 in 18/18 cells; C3 beam > whole in 18/18; C2 0 wrong adoptions, zero-loss replay exact with sync 1.0 in every run. B = 29 reported as the declared tie |
| **10 · Domains with partners** | `partners5.py` (K.6, K.11, K.16) | pair worlds 5375 (+500); pairs (v, v+1), v = 1, 3, …, 19 | R1–R7 of PARTNERS5 on the 10 cells: R1 joined > best alone ≥ 9/10; R2 joined > notubes ≥ 9/10; R3 mean gain > 0 and ≥ 7/10 positive; R4 every organism ≥ itself alone 10/10; R5 0 landed above a bound; R6 pool ≤ 4n; R7 transferred need ≥ 0.90 |
| **All laws as mathematics** | `laws6.py` (K.8, K.16, K.17) | world 5340; all 21 shades | every LAWS6 criterion (EXACT; L0, L1′, L1, L2, LE, L4, L5, L3, C2 ≥ 90 % of in scope; C1 0 conflicts; PR ≥ 2/3 cells negative and mean < 0; RC both ≥ 90 %) **and** the Law 4 noise-free check: on the 11 odd shades x world 5340, the organism v5m with every need measured by the full own-policy fork with common randomness (no open-loop replay), landing precision ≥ 0.90 in ≥ 10/11 |
| **12 ORG7 rows pending re-check** (Information theory v20, Protocol theory v18, Databases v9, Ledgers v7, Human reasoning v5, Linguistics v16, Earth and space v11, Level B v19; Mathematics: operator algebra, Distributed systems, Mathematics (domain), Level C: all 21) | `org8run.py` = ORG7 with the budget-correct counter-shift (`laws3.run_st3`); ORG7 measures unchanged (`analyze_org8.py`) | evaluation 5300–5311 (12), worlds 5320, random structures 530000+ | the row's shade(s) green under ORG8 by ORG7's own rule (all of m1–m6 and control); centre rows: all 21 green. A row that fails returns to "started" with its ORG8 numbers |
Not in this seal: Meaning, D, E (re-seal after the heterogeneous host), ENGINE3 and the agent product (real models →
real-tools step), road 3 and "open the gate" (owner decisions).

## Run (owner's laptop; four PowerShell windows; ~12 h estimated, resumable)
`seal1.py` balances 86 units over 4 windows (estimates: verify 100 min, laws collect 35, laws local 20, partners 40,
ORG8 10, beam 30 per unit). After all four print `WINDOW n FINISHED`: `python seal1.py analyze` → `RESULTS_SEAL1.md`.
Smoke test before sealing: 4-tick worlds into a temporary folder, deleted (no seal seed's result kept or read).
