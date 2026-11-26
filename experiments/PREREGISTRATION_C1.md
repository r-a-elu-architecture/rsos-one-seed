# C1 pre-registration: communication speed, the node palace and the green-dot signal

Written and committed before the run. Mission (owner, 17 Nov 2026): human ↔ AI, platform ↔ product and AI ↔ AI
communicate much faster in the RSOS language. Until now that was never measured (MISSION_ANALYSIS.md, omission M1).

## Carriers (the same meaning in each)

| Carrier | What is sent |
|---|---|
| JSON | Compact canonical IR (the A2A-style structured payload baseline) |
| JSON+gzip | Same, gzip level 9 |
| RSOS | The program text |
| RSOS+gzip | Same, gzip level 9 |
| JSON-diff | Line diff of pretty canonical IR against the shared library IR (strong delta baseline) |
| Palace | `@symbol#hash` + line edits against the shared book (src/rsoslang/palace.py) |

Messages: 7 example programs as shared books; 40 compiling variants of each (1–3 edits: numbers, Morse codes,
deleting a CUE/FUTUREPACE line), seed 20261117. Size = UTF-8 bytes; tokens = regex `\w+|[^\w\s]` (proxy: no
tokenizer package available offline). Fidelity = SHA-256 IR digest equal to the sender's.

Haptic: each message as International Morse (unit timing 1/3/1/3/7), seconds at 10 wpm (unit = 0.12 s).

Drift: the receiver's book differs from the sender's by 1 or 3 edits. Arms: unchecked (apply edits blindly),
checked (hash signal = green dot), healed (White Dragon find/heal: chunk hashes of 4 lines, only the mismatching
chunks are resent).

## Predictions (pass/fail fixed now)

- P1: median RSOS / JSON bytes ≤ 0.50.
- P2: in-sync palace: exact decode 100%, median Palace / RSOS bytes ≤ 0.10.
- P3: median Palace bytes < median RSOS+gzip bytes.
- P4: median Palace bytes < median JSON-diff bytes.
- P5: drift, unchecked: exact < 50%. Checked: drift detected 100%, no silent wrong decode.
- P6: healed: exact 100% and median heal bytes ≤ 0.50 × a full RSOS resend.
- P7: haptic at 10 wpm: median full RSOS program > 120 s, median palace message < 15 s.

Negative results are recorded as they come.
