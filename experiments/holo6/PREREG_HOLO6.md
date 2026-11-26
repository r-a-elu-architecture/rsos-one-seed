# HOLO6 preregistration: the particle lands live, at the letter (owner 13:00, U159-U164)

Sealed before the test. Follows HOLO5 (sealed result: 0 landings, because no bucketed address predicted where a
healing choice exists; a healing choice did exist at ~27 % of letters read).

## Change from HOLO5 (one change)
The address is the letter itself. At every dispatch with disagreeing lenses, in the world being run, the world is
frozen, each different choice is run to the end from its own copy (past = trace, present = frozen state, future =
the copies), and the particle lands on the choice that heals the whole with no channel worse (U164, heals() from the
sealed holo5.py, hash-checked). Otherwise the unhealed quark (DNA0) runs. No training, no knobs: nothing global changes.

## Disclosures
- Smoke runs on seed 900 (outside training and test) for timing found a bug (a single ready process was not
  dispatched); fixed before this seal.
- Layer note: the frozen copy contains the world's own future (future bursts). That is a layer-2 property (state can
  be frozen and copied). A layer-1 scheduler would need a model of the future in its place: transfer is a separate test.
- In a deterministic host, choosing an action whose future is better than the quark's own continuation cannot make the
  whole worse than the unhealed quark (policy-improvement argument). W4 is therefore expected; the open questions
  are W1, W2, W3, W5.

## Test (once, fresh seeds 500-515, same worlds as HOLO4 and HOLO5)
| # | Prediction (one-sided sign tests, p < 0.05) |
|---|---|
| W1 | live landing beats the best of round-robin and history at d = 5 |
| W2 | its advantage grows with relation density (Spearman > 0, p < 0.05) |
| W3 | coupled chain beats parts summed at d = 5 (live landing in both) |
| W4 | live landing beats unhealed, all densities pooled |
| W5 | live landing beats HOLO4 global-knob healing, all densities pooled |
