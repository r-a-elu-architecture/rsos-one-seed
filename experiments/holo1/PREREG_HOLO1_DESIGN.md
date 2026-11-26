# HOLO1 design: the whole hypothesis tested fully in layer 2 (private, 21 Nov 2026 11:05; design, to be sealed by
# the next account before any run). Source: owner 10:46 (corpus/chat-5/layers_turns_21nov.md), HANDOFF 3a/3b.

Layer 2 = an open model run locally on the owner's laptop (e.g. via Ollama), where the whole internal state
(hidden states of every layer at every token, KV cache, seed, context) is frozen, copied and compared exactly.
Agents A and B = two instances of the same model, each with its own context ("body" and "environment").

| ID | Hypothesis part (owner) | Test in layer 2 | Prediction to seal |
|---|---|---|---|
| H1 | Whole-state snapshot, unique each instant | Snapshot all hidden states per token; distance between consecutive snapshots | Every snapshot differs (distance > 0); 0 identical pairs |
| H2 | Words are produced by the whole state | A in two different states (two contexts) is steered to emit the **same sentence** ("go to eat the soup"); compare A's hidden states at emission | States differ while words are identical |
| H3 | **Hologram message:** words carry the sender's state | B receives the identical sentence from A-state-1 vs A-state-2 (words only, plus the token-level traces such as preceding phrasing); measure B's state change | B's state change differs between the two senders beyond the noise floor (repeat seeds) |
| H4 | Receiver's state decides the effect (VAKOG chain) | Prime B into two states (village-soup memory vs neutral); send the same words | B's state change and reply depend on its prior state |
| H5 | Full hologram > words | B receives words + A's hidden state (injected as a steering vector) vs words only | Transfer toward A's state is larger with the hologram |
| H6 | Cascade through all domains | Change one token early in a multi-agent, multi-domain simulation (kitchen, computer, company, family, school); track divergence over steps | Divergence grows along the chain at some nodes and fades at others; record which |
| H7 | Infinite seed / lineage | Attribute a late state to earlier inputs (ablate each earlier turn) | Every earlier turn has a non-zero effect on the late state |
| H8 | One family | Compare internal representations of the domains (philosophy, chemistry, biology, technology, family) | Shared structure across domains above a shuffled baseline |

Rules: thresholds and noise floors fixed in the sealed version before running; code hashed and pushed; Bitcoin stamp;
results reported whether they pass or fail. Run node by node on the map (N11 mirror first: A and B).
