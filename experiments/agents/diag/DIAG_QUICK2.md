# quick2 diagnosis (23 Nov 2026 03:35; development seeds staff 6000-6029, orders 4000-4029; descriptive)
Go rule result: G1 PASS (no-answers at react's level: the phase 3 budget failure is fixed), G3 PASS, G2 FAIL (rsos2 vs react
11/13 pooled; Llama 5/10, gpt-oss-20b 6/3). Noise floor: react vs identical react_b 13/7 (20 discordant of 120), Llama
react 0.900 vs react_b 0.800, with one pinned provider per model.
The 10 Llama losses to react, by cause (traces):
- 3 the early "answer now" prompt (2 calls before the end) cut runs short (B6013, B6021, C4009); react finished them in 10-12 calls.
- 6 verification said OK to a wrong answer after a different path (B6012, B6018, B6023, C4003, C4011, C4027); react_b also
  missed 3 of these -> path variance; Llama's self-check does not catch them.
- 1 tool-error loop ending wrong (B6015).
Strongest new signal: on Llama, runs with 2 or more failing tool calls in a row were correct 17/34; without such a streak
134/146 (all arms). gpt-oss-20b never had such a streak. The failing part is the longest failing run -> counter-shift (P1)
transfers from the organism to the agent host.
Build rsos3 = rsos2 + counter-shift on error streaks (>= 2) + 'answer now' only on the last call.

## quick3 (23 Nov 03:53; development seeds staff 6100-6129, orders 4100-4129; CAND=rsos3)
Go rule: G1 PASS, G2 PASS (rsos3 vs react 11/9), G3 PASS -> formally GO. But rsos3 vs react_b 13/15, and the noise floor
(react vs identical react_b) is 22 discordant of 120: the margin is inside the noise.
Accuracy Llama: react 0.750, react_b 0.800, rsos2 0.817, rsos3 0.750; gpt-oss-20b: 0.783, 0.800, 0.800, 0.817.
Counter-shift fired in 16 Llama runs, 10 correct (63 %); runs with an error streak in the other arms: react 4/13,
react_b 8/15, rsos2 9/13. Llama runs where it did not fire: rsos3 35/44 (80 %) vs react 41/47 (87 %).
Cost measured: ~2.4 M tokens for 480 runs (about $0.0007 per run).
Reading: the structure changes how a run fails (no-answers 0-2 vs react 8; streak runs recover more often), but the
accuracy effect is at most ~2-4 points, inside a noise floor of ~18 % discordant tasks between identical agents.
A long run of the planned size (1,800 runs) would most likely not decide. Not sealed; next step per the owner's method:
update the structural map to the post-ORG7 state, then the landing rule for each open problem (agents included).
