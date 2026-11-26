# HOLO2 results (private, 21 Nov 2026, (UTC+02:00) Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius)

Sealed first: `SEAL_HOLO2.txt` (commit 52daa63). Raw: `RESULTS_HOLO2.json`. 120 orders x 20 seeds.

## Scored exactly as sealed
| ID | Result | Verdict |
|---|---|---|
| P1a one subnode reaches all five | 24 of 120 orders (exactly the 24 orders that start with O) | **FAIL** |
| P1b the change grows over time | median growth 3.2x; 120 of 120 orders grow (range 1.65-11.6x) | **PASS** |
| P2 coupled beats parts and plain controller on G | best order (AVKOG) 0.5745 = uncoupled 0.5745; plain PI 0.5768 best; median order 0.5737; all 4 sign tests p = 1.0 | **FAIL** |
| P3 orders differ in G | Kruskal p = 0.997; range across orders 0.0027 < seed SD 0.005 | **FAIL** |
Recorded: computer's order V-A-K-O-G 0.5729; person's order V-O-K-G-A 0.5725; top orders all start with A, bottom all start with G.

## What the failures say (fever principle, diagnosed after the run)
1. **The host never got hot:** 0 of 600 steps above the overheating limit; A selected only "none" (451) or "fan" (149),
   never throttle. The G-endpoint barely moved (whole spread 0.5 %). The host did not stress the quark, so G could
   not tell assemblies apart. This is the host assembly, not the law.
2. **A first = uncoupled:** when A comes first it reads the raw signal, which is exactly the uncoupled build; those
   orders scored best. V and O before A made the alarm fire later or earlier than needed here: my V and O weights
   (assembled by me, not by the owner) did not fit this host.
3. **P1a:** the trigger in O moved the subnodes after O in the chain; it reached the ones before O only if the
   protocol changed, and in an unstressed host it rarely did. Where it travelled, it grew (P1b, all 120 orders).
Nothing here was tuned after the run. A next version (HOLO3) must be sealed before running: a host that is
stressed (overheating possible), and subnode weights fixed by the owner's reading, not by me.
