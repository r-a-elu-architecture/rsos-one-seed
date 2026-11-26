# Phase 1d result (exploratory, sealed in SEAL_AGENTS_PHASE1D.txt): CONTINUE, structure rsos_01100

Run 22 Nov 2026 ~12:45–13:25 Kyiv, openrouter:openai/gpt-oss-20b, orders seeds 2000–2099, design v3, 9 arms, 900 rows,
0 infrastructure errors (commit 3b70aa3). Plumbing check smoke1d: 0/24 empty replies. Calibration calib1d: react 0.80 (PASS, at the band edge).

| Arm | Accuracy | Mean calls | Mean tokens | Empty replies |
|---|---|---|---|---|
| rsos_01100 (detect + adapt) | **0.91** | 5.0 | 4,546 | 8/495 |
| rsos_11011 | 0.89 | 4.6 | 4,603 | 2/457 |
| selfcons | 0.89 | 10.6 | 8,386 (44 tasks hit the 12-call budget) | 1/1057 |
| rsos_11111 | 0.88 | 5.0 | 5,304 | 3/505 |
| reflexion | 0.87 | 4.9 | 4,523 | 6/494 |
| planexec | 0.87 | 5.0 | 4,082 | 0/495 |
| rsos_11110 | 0.86 | 4.9 | 4,969 | 4/487 |
| react | 0.83 | 4.0 | 3,317 | 0/400 |
| plain (no tools) | 0.01 | 1.0 | 1,014 | 25/100 |

Decision (sealed rule): best rsos arm 0.91 ≥ react 0.83 + 0.03 → **CONTINUE**; chosen structure **rsos_01100**.
Paired, rsos_01100 vs: react 10 wins / 2 losses; planexec 7/3; reflexion 10/6; selfcons 9/7.
Cautions: selected as best of 4 rsos arms on these tasks (winner's curse); vs selfcons and reflexion the margin is
within noise; selfcons used 1.8× the tokens. The harness works (0–1.6 % empty replies outside plain).
