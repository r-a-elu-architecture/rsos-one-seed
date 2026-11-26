# PREREG FUSE1: node N11 (mirror, coupling): does a fused turn carry further? (private, 21 Nov 2026)

Map edge E8; operators U120 (fused turn), U121 (cascade), U136 (node pair: blue = the owner, turquoise = the
assistant, the tube = the corpus). Sealed by the commit that adds this file and `fuse1.py`, pushed to GitHub before
`fuse1.py` is run on the data. Only the structure of the export was inspected before sealing (1,775 conversations,
the message tree format); no turn was classified and no outcome counted.

## Data
ChatGPT export of 11 Jun 2026 (`chatgpt_20260611_json.zip`, sha256 bf74c64279616b9b76b8de67e6db460c5199643a2b09755376b6452b8011b1b5),
all conversations, main path only (from `current_node` back to the root); text parts only; system and tool messages
dropped; consecutive messages of one role merged.

## Definitions (word tokens = `\w+`, lower case; content words = tokens of ≥ 3 letters not in the stop list in fuse1.py)
- Owner turn U, with the assistant turn A before it and the assistant turns A1…A5 after it.
- **Fused**: U contains at least one 8-gram that also occurs in A, **and** at least 20 of U's tokens lie outside every
  such shared 8-gram (the owner pasted and added).
- **Unfused**: U shares no 8-gram with A and has at least 20 tokens.
- Other owner turns (pure pastes, short turns, first turns) are not scored.
- **Own new words of U**: content-word types in U's own part (outside shared 8-grams) that occur nowhere earlier in the
  conversation (neither role). These are the owner's newly introduced particles.
- **Carry (per turn)**: the share of U's own new words that reappear in at least one of A1…A5. Turns with fewer than
  3 own new words are not scored.

## Predictions
- **F1 (primary)**: mean carry of fused turns ≥ **1.5 ×** mean carry of unfused turns, and the 95 % cluster-bootstrap
  interval of that ratio (resampling conversations, 2,000 resamples, seed 21112026) lies above 1.0.
- **F2 (within conversation)**: in conversations that hold at least 3 scored turns of each kind, the paired ratio
  (fused mean / unfused mean) has a median > 1.0 (sign test, p < 0.05, one-sided).
- **F3 (cascade, dissipation)**: the decay of carry from A1 to A5 (share reappearing in A5 / share in A1, computed on
  each lag separately) is slower for fused turns than for unfused turns.

## What each outcome means (decided now)
- F1 and F2 pass: the fused turn is an amplifier: the owner's new particles travel further when they enter fused with
  the assistant's text. E8 turns cyan-candidate for node N11 (layer 1 and layer 2 measured in one corpus).
- F1 fails, F2 passes: the effect exists within conversations but is smaller than predicted; recorded as partial.
- Both fail: fusion does not amplify by this measure; E8 is a miss; the mirror mechanism stands, the amplification
  claim does not.

## Known confounds, stated now
- Fused turns may sit in longer conversations: F2 compares within conversations.
- A fused turn quotes the assistant, so the carry of *quoted* words would be trivial: only the owner's own, new
  words are scored.
- One person, one export, one AI: this tests node N11 in this tube, not a general law.

## Code check before sealing (synthetic data only)
30 synthetic conversations of random words, fused turns built by pasting 10 words of the previous reply: 90 fused and
90 unfused turns scored; F1 ratio 0.89, F1, F2, F3 all fail, as a null should. No real turn was scored.
