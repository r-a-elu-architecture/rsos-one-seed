# C1: communication speed, the node palace and the green-dot signal

Pre-registration: `experiments/PREREGISTRATION_C1.md` (commit ca35d5f, before the run).
Code: `experiments/c1_communication.py`, `src/rsoslang/palace.py`. Result: `results/c1_communication.json`,
results_sha256 `0331007ddae1ded72b9d2cb994bf34be369d2ee0fc568aa5044e5f3492d27158` (rerun reproduced the same hash).

280 messages (7 books × 40 compiling variants, 1–3 edits each); 366 drift cases (receiver's book 1 or 3 edits off).

## Size of one meaning, by carrier (medians)

| Carrier | Bytes | Tokens (regex proxy) | Haptic Morse at 10 wpm |
|---|---|---|---|
| JSON IR (compiled, with derived fields) | 7,101 | 3,292 | 11,118 s (3.1 h) |
| JSON IR + gzip | 1,434 | — | — |
| RSOS program | 896 | 172 | 991 s (16.5 min) |
| RSOS + gzip | 522 | — | — |
| JSON line-diff against the shared IR (strong delta baseline) | 97 | — | — |
| **Palace message** (`@symbol#hash` + line edits) | **65** | **14** | 84 s |

## Checks

| | Prediction | Result | |
|---|---|---|---|
| P1 | RSOS ≤ 0.50 × JSON | 0.124 | Pass |
| P2 | In sync: exact 100%, palace ≤ 0.10 × RSOS | 280/280 exact; 0.066 | Pass |
| P3 | Palace < RSOS+gzip | 65 < 522 | Pass |
| P4 | Palace < JSON-diff | 65 < 97 | Pass |
| P5 | Drift: blind exact < 50%; detected 100%; no silent wrong decode | blind 23.8%; detected 366/366; 0 silent | Pass |
| P6 | Heal exact 100%, ≤ 0.50 × full resend | 366/366; 0.36 (1 edit 0.28, 3 edits 0.41) | Pass |
| P7 | Haptic: program > 120 s and palace < 15 s | 991 s; **84 s** | **Fail** |

Every decode is checked by the receiver recompiling the program: the SHA-256 IR digest includes the governance
diagnostics, so the consent and Spine checks travel through compression intact (the property ChatGPT's EXP-008
needed a separate constraint for: 77/379 safe unconstrained, c2 T9.100).

## What the numbers mean

1. **The speed gain is the palace, not the syntax.** A symbol that opens a book both sides already hold carries a
   whole program in 14 tokens: 1.1% of the compiled JSON, 7% of the program text, and smaller than gzip or a JSON
   diff against the same shared state. This is the owner's "palace of all books for that node" and c2 T28's "a compact
   cue retrieves a larger structure", made exact.
2. **Without the green dot the palace is dangerous.** When the receiver's book has drifted, blind decoding is right
   only 23.8% of the time, and wrong silently the rest. The hash signal turned every one of those into a detected
   drift (366/366), and the find/heal step repaired every one at about a third of the cost of resending.
3. **Felt glyph-by-glyph Morse is too slow for programs (P7 failed).** Even the 14-token palace message takes 84 s
   on the wrist. The felt channel must carry symbols (one short code = one book, as the cue framework's 5 codes do),
   not spelled text. Per-symbol at the existing code lengths (1–3 elements) would be a few seconds; that is a
   calculation, not yet a measurement.

## Honest limits

- **The JSON baseline is generous to RSOS.** The compiled IR carries derived fields. Post-hoc (not pre-registered):
  against a minimal JSON of the parsed statements, RSOS text is 0.56× (range 0.52–0.70). P1 would fail against that
  baseline. The palace result (P2–P4) does not depend on it.
- Delta coding against a shared library is known engineering (rsync, git, JSON Patch). What is new here is the
  combination: symbol + signal + heal inside a typed, governed language, where decoding re-runs the safety checks.
- Tokens are a regex proxy (no tokenizer installed offline). No LLM decoded anything here: natural language and
  cross-model decoding (c2 T3) remain untested and need API access.
- The books are the 7 example programs; variants are small edits. Real traffic would have larger edits and more
  books.
